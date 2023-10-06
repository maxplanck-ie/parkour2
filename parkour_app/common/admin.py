from authtools.admin import NamedUserAdmin
from authtools.forms import UserCreationForm
from common.models import CostUnit, Duty, Organization, PrincipalInvestigator
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.utils.crypto import get_random_string
from django.utils.encoding import force_str
from django.utils.translation import gettext as _
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter

User = get_user_model()


class DefaultListFilter(SimpleListFilter):
    all_value = "_all"

    def default_value(self):
        raise NotImplementedError()

    def queryset(self, request, queryset):
        if (
            self.parameter_name in request.GET
            and request.GET[self.parameter_name] == self.all_value
        ):
            return queryset

        if self.parameter_name in request.GET:
            return queryset.filter(
                **{self.parameter_name: request.GET[self.parameter_name]}
            )

        return queryset.filter(**{self.parameter_name: self.default_value()})

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == force_str(lookup)
                or (
                    self.value() == None
                    and force_str(self.default_value()) == force_str(lookup)
                ),
                "query_string": cl.get_query_string(
                    {
                        self.parameter_name: lookup,
                    },
                    [],
                ),
                "display": title,
            }
        yield {
            "selected": self.value() == self.all_value,
            "query_string": cl.get_query_string(
                {self.parameter_name: self.all_value}, []
            ),
            "display": _("All"),
        }


class ArchivedFilter(DefaultListFilter):
    title = _("Archived ")
    parameter_name = "archived__exact"

    def lookups(self, request, model_admin):
        return ((False, "No"), (True, "Yes"))

    def default_value(self):
        return False


class CostUnitInline(admin.TabularInline):
    model = CostUnit
    extra = 1


@admin.register(PrincipalInvestigator)
class PrincipalInvestigatorAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "archived")
    search_fields = (
        "name",
        "organization__name",
    )
    list_filter = ("organization", ArchivedFilter)
    inlines = [CostUnitInline]

    actions = (
        "mark_as_archived",
        "mark_as_non_archived",
    )

    @admin.action(description="Mark as archived")
    def mark_as_archived(self, request, queryset):
        queryset.update(archived=True)

    @admin.action(description="Mark as non-archived")
    def mark_as_non_archived(self, request, queryset):
        queryset.update(archived=False)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    pass


@admin.register(CostUnit)
class CostUnitAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "pi",
    )
    search_fields = (
        "name",
        "pi__name",
        "pi__organization__name",
    )
    list_filter = (
        ("pi", RelatedDropdownFilter),
        ("pi__organization", RelatedDropdownFilter),
        (ArchivedFilter),
    )

    actions = (
        "mark_as_archived",
        "mark_as_non_archived",
    )

    @admin.action(description="Mark as archived")
    def mark_as_archived(self, request, queryset):
        queryset.update(archived=True)

    @admin.action(description="Mark as non-archived")
    def mark_as_non_archived(self, request, queryset):
        queryset.update(archived=False)


class UserCreationForm(UserCreationForm):
    """
    A UserCreationForm with optional password inputs.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].required = False
        self.fields["password2"].required = False
        # If one field gets autocompleted but not the other, our 'neither
        # password or both password' validation will be triggered.
        self.fields["password1"].widget.attrs["autocomplete"] = "off"
        self.fields["password2"].widget.attrs["autocomplete"] = "off"

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = super().clean_password2()
        if bool(password1) ^ bool(password2):
            raise forms.ValidationError("Fill out both fields")
        return password2


@admin.register(User)
class UserAdmin(NamedUserAdmin):
    add_form = UserCreationForm
    add_fieldsets = (
        (
            None,
            {
                "description": (
                    "Enter the new user's name and email address and click Save."
                    " The user will be emailed a link allowing him/her to login to"
                    " the site and set his/her password."
                ),
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                ),
            },
        ),
        (
            "Password",
            {
                "description": "Optionally, you may set the user's password here.",
                "fields": ("password1", "password2"),
                "classes": ("collapse", "collapse-closed"),
            },
        ),
    )

    list_display = (
        "first_name",
        "last_name",
        "email",
        "phone",
        "organization",
        "pi",
        "cost_units",
        "is_staff",
    )

    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone",
        "organization__name",
        "pi__name",
        "cost_unit__name",
    )

    list_filter = (
        "is_staff",
        "organization",
        ("pi", RelatedDropdownFilter),
    )
    list_display_links = (
        "first_name",
        "last_name",
        "email",
    )
    filter_horizontal = (
        "cost_unit",
        "groups",
        "user_permissions",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "password",
                ),
            },
        ),
        (
            "Personal info",
            {
                "fields": (
                    "phone",
                    "organization",
                    "pi",
                    "cost_unit",
                ),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_pi",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Other",
            {
                "fields": ("last_login",),
            },
        ),
    )

    def cost_units(self, obj):
        cost_units = obj.cost_unit.all().values_list("name", flat=True)
        return ", ".join(sorted(cost_units))

    def save_model(self, request, obj, form, change):
        if not change and (
            not form.cleaned_data["password1"] or not obj.has_usable_password()
        ):
            # Django's PasswordResetForm won't let us reset an unusable
            # password. We set it above super() so we don't have to save twice.
            obj.set_password(get_random_string(length=12))
            reset_password = True
        else:
            reset_password = False

        super().save_model(request, obj, form, change)

        if reset_password:
            reset_form = PasswordResetForm({"email": obj.email})

            if reset_form.is_valid():
                reset_form.save(
                    request=request,
                    from_email=settings.SERVER_EMAIL,
                    use_https=request.is_secure(),
                    subject_template_name="registration/" + "user_creation_subject.txt",
                    email_template_name="registration/" + "user_creation_email.html",
                )


@admin.register(Duty)
class DutyAdmin(admin.ModelAdmin):
    list_display = (
        "main_name",
        "backup_name",
        "start_date",
        "end_date",
        "facility",
        "platform",
        "comment",
        "archived",
    )
    search_fields = ("main_name", "backup_name", "facility", "comment")
    list_filter = ("facility", ArchivedFilter)
    actions = (
        "mark_as_archived",
        "mark_as_non_archived",
    )

    @admin.action(description="Mark as archived")
    def mark_as_archived(self, request, queryset):
        queryset.update(archived=True)

    @admin.action(description="Mark as non-archived")
    def mark_as_non_archived(self, request, queryset):
        queryset.update(archived=False)


# admin.site.unregister(User)
