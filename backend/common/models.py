from datetime import datetime

from authtools.models import AbstractEmailUser
from django.conf import settings
from django.db import models


def get_deleted_org():
    return Organization.objects.get_or_create(email="deleted.org@example.com",
                                              first_name='Deleted',
                                              last_name='Organization')[0]


def get_deleted_pi():
    return User.objects.get_or_create(email="deleted.pi@example.com",
                                      first_name='Deleted',
                                      last_name='PI')[0]


class Organization(models.Model):
    name = models.CharField("Name", max_length=100)
    archived = models.BooleanField("Archived", default=False)

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
    archived = models.BooleanField("Archived", default=False)

    class Meta:
        abstract = True


class CostUnit(OrganizationMixin, models.Model):
    name = models.CharField("Name", max_length=100)
    pi = models.ForeignKey(
        'User',
        verbose_name="Principal Investigator",
        on_delete=models.SET(get_deleted_pi),
    )

    archived = models.BooleanField("Archived", default=False)


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

    @property
    def facility(self):
        # if self.pi is None:
        #     membership = None
        # elif self.pi.name == settings.BIOINFO:
        #     membership = "Bioinfo"
        # elif self.pi.name == settings.DEEPSEQ:
        #     membership = "DeepSeq"
        # else:
        #     membership = None
        # return membership

        # For IMB'S fork of Parkour, this is irrelevant
        return None

    @property
    def can_solicite_paperless_approval(self):
        # result_user = False
        # result_pi = False
        # if self.pi is not None and self.pi.email != "Unset":
        #     if (
        #         not '"' in self.pi.email
        #         and self.pi.email.split("@")[1] == settings.EMAIL_HOST
        #     ):
        #         result_pi = True
        #     if (
        #         not '"' in self.email
        #         and self.email.split("@")[1] == settings.EMAIL_HOST
        #     ):
        #         result_user = True
        # return result_user and result_pi

        # For IMB'S fork of Parkour, this is irrelevant 
        return False

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def member_of_bcf(self):
        return self.groups.filter(name=settings.BIOINFO).exists()


class Duty(models.Model):
    main_name = models.ForeignKey(
        User,
        on_delete=models.deletion.CASCADE,
        related_name="main_name",
        verbose_name="Responsible Person",
    )
    backup_name = models.ForeignKey(
        User,
        on_delete=models.deletion.CASCADE,
        related_name="backup_name",
        verbose_name="Backup Person",
        null=True,
        blank=True,
    )
    start_date = models.DateTimeField(
        "Start Date",
        default=datetime.now,
    )
    end_date = models.DateTimeField(
        "End Date",
        null=True,
        blank=True,
    )
    platform = models.CharField(
        "Platform",
        choices=[("short", "Short"), ("long", "Long"), ("shortlong", "Short + Long")],
        default="short",
        max_length=15,
    )
    comment = models.TextField(
        "Comment",
        max_length=2500,
        null=True,
        blank=True,
    )
    archived = models.BooleanField("Archived", default=False)

    class Meta:
        db_table = "duty"
        verbose_name = "Duty"
        verbose_name_plural = "Duties"
        ordering = ["end_date", "start_date"]


class DateTimeMixin(models.Model):
    create_time = models.DateTimeField("Create Time", auto_now_add=True)
    update_time = models.DateTimeField("Update Time", auto_now=True)

    class Meta:
        abstract = True
