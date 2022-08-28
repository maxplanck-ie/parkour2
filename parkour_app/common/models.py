from pyexpat import model
from authtools.models import AbstractEmailUser
from django.db import models


def get_deleted_org():
    return Organization.objects.get_or_create(name="deleted ORG")[0]


def get_deleted_pi():
    return PrincipalInvestigator.objects.get_or_create(name="deleted PI")[0]


class Organization(models.Model):
    name = models.CharField("Name", max_length=100)

    def __str__(self):
        return self.name


class PrincipalInvestigator(models.Model):
    name = models.CharField("Name", max_length=100)
    organization = models.ForeignKey(
        Organization, on_delete=models.SET(get_deleted_org)
    )
    parent_user = models.OneToOneField('User', on_delete=models.PROTECT, default=None, null=True)

    class Meta:
        verbose_name = "Principal Investigator"
        verbose_name_plural = "Principal Investigators"
        ordering = ["organization__name", "name"]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class CostUnit(models.Model):
    name = models.CharField("Name", max_length=100)
    pi = models.ForeignKey(
        PrincipalInvestigator,
        verbose_name="Principal Investigator",
        on_delete=models.SET(get_deleted_pi),
    )

    class Meta:
        verbose_name = "Cost Unit"
        verbose_name_plural = "Cost Units"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.pi.organization.name}: {self.pi.name})"


class OIDCGroup (models.Model):
    name = models.CharField("Name", max_length=200, unique=True)
    pi = models.ForeignKey(
        PrincipalInvestigator,
        verbose_name="Principal Investigator",
        on_delete=models.SET(get_deleted_pi),
    )

    class Meta:
        verbose_name = "OpenID Group"
        verbose_name_plural = "OpenID Groups"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        
        # Force group names to lower case
        self.name = self.name.strip().lower()

        super(OIDCGroup, self).save(force_insert, force_update, using, update_fields)


class User(AbstractEmailUser):
    first_name = models.CharField("First name", max_length=50)
    last_name = models.CharField("Last name", max_length=50)
    phone = models.CharField("Phone", max_length=50, null=True, blank=True)
    oidc_id = models.CharField("OIDC ID", max_length=255, null=True, unique=True, default=None, blank=True)
    is_bioinformatician = models.BooleanField('Is bioinformatician?', default=False)

    organization = models.ForeignKey(
        Organization,
        verbose_name="Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    pi = models.ManyToManyField(
        PrincipalInvestigator,
        verbose_name="Principal Investigator",
        blank=True,
    )

    cost_unit = models.ManyToManyField(
        CostUnit,
        verbose_name="Cost Unit",
        blank=True,
    )

    class Meta:
        db_table = "auth_user"
        ordering = ["last_name", "first_name"]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class DateTimeMixin(models.Model):
    create_time = models.DateTimeField("Create Time", auto_now_add=True)
    update_time = models.DateTimeField("Update Time", auto_now=True)

    class Meta:
        abstract = True
