from datetime import datetime

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


class User(AbstractEmailUser):
    first_name = models.CharField("First name", max_length=50)
    last_name = models.CharField("Last name", max_length=50)
    phone = models.CharField("Phone", max_length=50, null=True, blank=True)

    organization = models.ForeignKey(
        Organization,
        verbose_name="Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    pi = models.ForeignKey(
        PrincipalInvestigator,
        verbose_name="Principal Investigator",
        on_delete=models.SET_NULL,
        null=True,
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
        return f"{self.first_name} {self.last_name} ({self.email})"


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
    facility = models.CharField(
        "Facility",
        choices=[("bioinfo", "BioInfo"), ("deepseq", "DeepSeq")],
        default="bioinfo",
        max_length=7,
    )
    platform = models.CharField(
        "Platform",
        choices=[("short", "Short"), ("long", "Long")],
        default="short",
        max_length=5,
    )

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
