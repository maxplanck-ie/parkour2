from pyexpat import model
from authtools.models import AbstractEmailUser
from django.db import models


def get_deleted_org():
    return Organization.objects.get_or_create(name="deleted ORG")[0]


def get_deleted_pi():
    return User.objects.get_or_create(name="deleted PI")[0]


class Organization(models.Model):
    name = models.CharField("Name", max_length=100)

    def __str__(self):
        return self.name


class OrganizationMixin(models.Model):

    organization = models.ForeignKey(
        Organization,
        verbose_name="Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
    )

    class Meta:
        abstract = True


class CostUnit(OrganizationMixin, models.Model):
    name = models.CharField("Name", max_length=100)
    
    pi = models.ForeignKey(
        'User',
        verbose_name="Principal Investigator",
        on_delete=models.SET(get_deleted_pi),
    )

    obsolete = models.PositiveIntegerField("Obsolete", default=1)

    class Meta:
        verbose_name = "Cost Unit"
        verbose_name_plural = "Cost Units"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.organization})"


class OIDCGroup (models.Model):
    name = models.CharField("Name", max_length=200, unique=True)
    pi = models.ForeignKey(
        'User',
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
    is_bioinformatician = models.BooleanField(
        'Bioinformatician status',
        help_text='Designates whether a user is a bioinformatician.',
        default=False)
    is_pi = models.BooleanField(
        'Principal Investigator status',
        help_text='Designates whether a user is a Principal Investigator.',
        default=False)

    pi = models.ManyToManyField(
        'self',
        verbose_name="Principal Investigator",
        symmetrical=False,
        blank=True,
    )

    is_pi = models.BooleanField("PI Account", default=False)

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
        return f"{self.first_name} {self.last_name}"
    
    @property
    def member_of_bcf(self):
        return self.groups.filter(name='Bioinfo-CF').exists()


class DateTimeMixin(models.Model):
    create_time = models.DateTimeField("Create Time", auto_now_add=True)
    update_time = models.DateTimeField("Update Time", auto_now=True)

    class Meta:
        abstract = True
