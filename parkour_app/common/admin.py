from authtools.admin import NamedUserAdmin
from authtools.forms import UserCreationForm, UserChangeForm
from common.models import CostUnit, Organization, OIDCGroup
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.utils.crypto import get_random_string
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin

User = get_user_model()


class CostUnitInline(admin.TabularInline):
    model = CostUnit
    fields = ('name', 'organization', 'obsolete',)
    extra = 1

@admin.register(CostUnit)
class CostUnitAdmin(admin.ModelAdmin):

    def has_module_permission(self, request):
        return False


class OIDCGroupInline(admin.TabularInline):
    model = OIDCGroup
    extra = 1

@admin.register(OIDCGroup)
class OIDCGroupAdmin(admin.ModelAdmin):

    def has_module_permission(self, request):
        return False


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):

    def has_module_permission(self, request):
        return False


class CheckUserEmailExtension:
    def clean_email(self):
        email = self.cleaned_data.get("email")

        if email:
            if 'imb.de' in email:
                raise forms.ValidationError("Use the full email extension imb-mainz.de, not just imb.de")
        return email


class UserCreationForm(UserCreationForm, CheckUserEmailExtension):
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


class UserChangeForm(UserChangeForm, CheckUserEmailExtension):
    pass


@admin.register(User)
class UserAdmin(NamedUserAdmin):
    inlines = [CostUnitInline, OIDCGroupInline]
    form = UserChangeForm
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
                    "is_pi",
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
        "organizations",
        "pis",
        "pi_status",
        "staff_status",
        'bioinformatician_status',
    )

    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone",
        "costunit__organization__name",
        "pi__last_name",
    )

    list_filter = (
        "is_staff",
        "costunit__organization__name",
    )
    list_display_links = (
        "first_name",
        "last_name",
        "email",
    )
    autocomplete_fields = (
        "groups",
        "pi",
    )
    filter_horizontal = (
        "user_permissions",
    )

    def pis(self, obj):
        return ", ".join(sorted([pi.full_name for pi in obj.pi.all()]))

    def pi_status(self, obj):
        return obj.is_pi
    pi_status.boolean = True
    pi_status.short_description = "PI?"
    pi_status.admin_order_field = 'is_pi'

    def staff_status(self, obj):
        return obj.is_staff
    staff_status.boolean = True
    staff_status.short_description = "Staff?"
    staff_status.admin_order_field = 'is_staff'

    def bioinformatician_status(self, obj):
        return obj.is_bioinformatician
    bioinformatician_status.boolean = True
    bioinformatician_status.short_description = "BioInfo?"
    bioinformatician_status.admin_order_field = 'is_bioinformatician'

    def organizations(self, obj):
        try:
            return ', '.join(obj.costunit_set.all().
                             order_by('organization__name').
                             values_list('organization__name', flat=True).
                             distinct())
        except:
            return ''

    def add_view(self, request, extra_context=None):
        self.inlines = []
        return super().add_view(request)

    def change_view(self, request, object_id, extra_context=None):
        
        self.inlines = []
        obj = self.model.objects.get(id=object_id)
        if obj.is_pi:
            self.inlines = [CostUnitInline, OIDCGroupInline]

        if request.user.is_superuser:
            self.fieldsets = (
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
                            "is_pi",
                            "pi",
                        ),
                    },
                ),
                (
                    "Permissions",
                    {
                        "fields": (
                            "is_active",
                            "is_staff",
                            "is_bioinformatician",
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
        else:
            self.fieldsets = (
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
                            "is_pi",
                            "pi",
                        ),
                    },
                ),
                (
                    "Permissions",
                    {
                        "fields": (
                            "is_active",
                            "is_staff",
                            "is_bioinformatician",
                            "groups",
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

        return super().change_view(request, object_id)

    def get_search_results(self, request, queryset, search_term):

        if request.GET.get('field_name', '') == 'pi':
            queryset, use_distinct = super(UserAdmin, self).get_search_results(request, queryset, search_term)
            return queryset.filter(is_pi=True), use_distinct

        return super().get_search_results(request, queryset, search_term)

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


# admin.site.unregister(User)

admin.site.unregister(Group)
@admin.register(Group)
class CustomGroupAdmin(GroupAdmin):
    
    def has_module_permission(self, request):
        if not request.user.is_superuser:
            return False
        return True