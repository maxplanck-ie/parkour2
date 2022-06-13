from django.contrib import admin
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.utils.crypto import get_random_string
from authtools.admin import NamedUserAdmin
from authtools.forms import UserCreationForm
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter

from common.models import PrincipalInvestigator, Organization, CostUnit

User = get_user_model()


class CostUnitInline(admin.TabularInline):
    model = CostUnit
    extra = 1


@admin.register(PrincipalInvestigator)
class PrincipalInvestigatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization',)
    search_fields = ('name', 'organization__name',)
    list_filter = ('organization',)
    inlines = [CostUnitInline]


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    pass


@admin.register(CostUnit)
class CostUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'pi',)
    search_fields = ('name', 'pi__name', 'pi__organization__name',)
    list_filter = (('pi', RelatedDropdownFilter),
                   ('pi__organization', RelatedDropdownFilter),)


class UserCreationForm(UserCreationForm):
    """
    A UserCreationForm with optional password inputs.
    """

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        # If one field gets autocompleted but not the other, our 'neither
        # password or both password' validation will be triggered.
        self.fields['password1'].widget.attrs['autocomplete'] = 'off'
        self.fields['password2'].widget.attrs['autocomplete'] = 'off'

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = super(UserCreationForm, self).clean_password2()
        if bool(password1) ^ bool(password2):
            raise forms.ValidationError('Fill out both fields')
        return password2


class UserAdmin(NamedUserAdmin):
    add_form = UserCreationForm
    add_fieldsets = (
        (None, {
            'description': (
                "Enter the new user's name and email address and click Save."
                " The user will be emailed a link allowing him/her to login to"
                " the site and set his/her password."
            ),
            'fields': ('first_name', 'last_name', 'email',),
        }),
        ('Password', {
            'description': "Optionally, you may set the user's password here.",
            'fields': ('password1', 'password2'),
            'classes': ('collapse', 'collapse-closed'),
        }),
    )

    list_display = ('first_name', 'last_name', 'email', 'phone',
                    'organization', 'pi', 'cost_units', 'is_staff',)

    search_fields = ('first_name', 'last_name', 'email', 'phone',
                     'organization__name', 'pi__name', 'cost_unit__name',)

    list_filter = ('is_staff', 'organization', ('pi', RelatedDropdownFilter),)
    list_display_links = ('first_name', 'last_name', 'email',)
    filter_horizontal = ('cost_unit', 'groups', 'user_permissions',)

    fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'email', 'password',),
        }),
        ('Personal info', {
            'fields': ('phone', 'organization', 'pi', 'cost_unit',),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups',
                       'user_permissions',),
        }),
        ('Other', {
            'fields': ('last_login',),
        }),
    )

    def cost_units(self, obj):
        cost_units = obj.cost_unit.all().values_list('name', flat=True)
        return ', '.join(sorted(cost_units))

    def save_model(self, request, obj, form, change):
        if not change and (not form.cleaned_data['password1'] or not
                           obj.has_usable_password()):
            # Django's PasswordResetForm won't let us reset an unusable
            # password. We set it above super() so we don't have to save twice.
            obj.set_password(get_random_string())
            reset_password = True
        else:
            reset_password = False

        super(UserAdmin, self).save_model(request, obj, form, change)

        if reset_password:
            reset_form = PasswordResetForm({'email': obj.email})

            if reset_form.is_valid():
                reset_form.save(
                    request=request,
                    from_email=settings.SERVER_EMAIL,
                    use_https=request.is_secure(),
                    subject_template_name='registration/' +
                    'user_creation_subject.txt',
                    email_template_name='registration/' +
                    'user_creation_email.html',
                )


admin.site.register(User, UserAdmin)
