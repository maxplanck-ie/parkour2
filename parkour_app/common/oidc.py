from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.contrib.auth.models import Group
from django.conf import settings
from common.models import User
from django.core.mail import send_mail
from django.urls import reverse
from django.template.loader import render_to_string
from common.models import Organization
from django.contrib.sites.shortcuts import get_current_site
from common.gcf_group_permissions import GROUP_PERMISSIONS


class ParkourOIDCAuthenticationBackend(OIDCAuthenticationBackend):

    def user_belongs_to_groups(self, user_groups, groups):
        """Check if any group assigned to a user is found in a list
        of groups."""
        
        return any(g in user_groups for g in groups)
    
    def verify_claims(self, claims):
        """Verify the provided claims to decide if authentication should be allowed.
           Only users that belong to one of the groups in OIDC_ALLOWED_GROUPS can 
           sign in.
        """ 

        # Check that the user is part of one of the allowed OIDC groups
        if settings.OIDC_ALLOWED_GROUPS:
            user_groups = claims.get('role', [])
            if not self.user_belongs_to_groups(user_groups, settings.OIDC_ALLOWED_GROUPS):
                return False

        # Otherwise carry out the default checks
        return super(ParkourOIDCAuthenticationBackend, self).verify_claims(claims)
    
    def filter_users_by_claims(self, claims):

        # sub is a unique user's ID, any other attribute, including email could change
        # therefore, try to identify a user first using sub
        oidc_id = claims.get('sub')
        if oidc_id:
            users = self.UserModel.objects.filter(oidc_id=oidc_id)
            if users:
                return users

        # Otherwise try the default way
        return super(ParkourOIDCAuthenticationBackend, self).filter_users_by_claims(claims)
        
    def send_email_new_user(self, user, claims=None):

        """Send an email to the staff when a new user is created
        automatically via the OIDC backend"""

        # URL for the admin page of the newly created users
        current_site = get_current_site(self.request)
        user_admin_change_url = f'{self.request.scheme + "://" if self.request.scheme else ""}{current_site}{reverse("admin:common_user_change", args=(user.id,))}'
        
        # Recipient list, all lab managers plus tUhe site admin
        recipients = self.UserModel.objects.filter(is_active=True, is_staff=True, groups__name='Genomics-CF').values_list('email', flat=True)

        # Get list of OIDC groups, if available
        oidc_groups = claims.get('role', [])
        oidc_groups.sort()


        send_mail(
                subject=f"{settings.EMAIL_SUBJECT_PREFIX} A new user was automatically created via OpenID authentication",
                message="",
                html_message=render_to_string(
                    "email/new_user_created_email.html",
                    {
                        "user": user,
                        "user_admin_change_url": user_admin_change_url,
                        "oidc_groups": oidc_groups
                    },
                ),
                from_email=settings.SERVER_EMAIL,
                recipient_list= recipients,
            )

    def create_user(self, claims):
        """Return object for a newly created user account."""

        # Get relevant user's attributes, if available
        email = claims.get('email', '')
        first_name = claims.get('given_name', '')
        last_name = claims.get('family_name', '')
        oidc_id = claims.get('sub')
        user_groups = claims.get('role', [])
        
        # Create user
        user = self.UserModel.objects.create_user(email=email,
                                                  first_name=first_name,
                                                  last_name=last_name,
                                                  is_active=True,
                                                  oidc_id=oidc_id,
                                                  )
        # Set an unusable password so that it cannot be changed
        user.set_unusable_password()

        # If a user belong to the Genomics CF set is_staff = True and add them to Genomics-CF
        if self.user_belongs_to_groups(user_groups, settings.OIDC_GENOMICSCF_GROUPS):
            user.is_staff = True
            gcf_group, gcf_group_created = Group.objects.get_or_create(name='Genomics-CF')
            if gcf_group_created:
                gcf_group.permissions.add(*GROUP_PERMISSIONS)
            user.groups.add(gcf_group)
        
        # For BCF (bioinformatics core facility) staff set is_bioinformatician to True
        # and assign them to the Bioinfo-CF group
        elif self.user_belongs_to_groups(user_groups, settings.OIDC_BIOINFOCF_GROUPS):
            user.is_bioinformatician = True
            bcf_group, _ = Group.objects.get_or_create(name='Bioinfo-CF')
            user.groups.add(bcf_group)
        
        else:
            # For regular users, try to assign a PI and organization based on
            # their OIDC groups
            try:
                pis = User.objects.filter(oidcgroup__name__in=user_groups, is_pi=True).distinct()
            except:
                pis = None
            if pis:
                user.pi.add(*list(pis))
                # user.cost_unit.add(*list(CostUnit.objects.filter(pi__in=pis).distinct()))
                try:
                    organization = Organization.objects.filter(id__in=pis.values_list('organization__id', flat=True)).distinct().get()
                    user.organization = organization
                except:
                    pass

        user.save()

        # Notify relevant staff that a new user was created
        self.send_email_new_user(user, claims)

        return user

    def update_user(self, user, claims):
        """Update existing user with new claims, if necessary save, and return user"""

        # Get relevant claims, if available
        email = claims.get('email', '')
        first_name = claims.get('given_name', '')
        last_name = claims.get('family_name', '')
        oidc_id = claims.get('sub')
        
        # Update fields
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.oidc_id = oidc_id
        user.save()

        return user