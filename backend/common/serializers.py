from rest_framework.serializers import ModelSerializer
from .models import (
    LoadFlowcellsTemplate,
    LibrariesAndSamplesTemplate,
    IncomingLibrariesSamplesTemplate,
    LibraryPreparationTemplate,
    PoolingTemplate,
    RunStatisticsTemplate,
    SequencesStatisticsTemplate,
)

from .models import CostUnit, Duty, User


class CostUnitSerializer(ModelSerializer):
    class Meta:
        model = CostUnit
        fields = ("id", "name")


class DutySerializer(ModelSerializer):
    class Meta:
        model = Duty
        fields = "__all__"


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "facility", "phone", "email")


class LibrariesAndSamplesTemplateSerializer(ModelSerializer):
    class Meta:
        model = LibrariesAndSamplesTemplate
        fields = ["id", "name", "file", "uploaded_at"]


class IncomingLibrariesSamplesTemplateSerializer(ModelSerializer):
    class Meta:
        model = IncomingLibrariesSamplesTemplate
        fields = ["id", "name", "file", "uploaded_at"]


class LibraryPreparationTemplateSerializer(ModelSerializer):
    class Meta:
        model = LibraryPreparationTemplate
        fields = ["id", "name", "file", "uploaded_at"]


class PoolingTemplateSerializer(ModelSerializer):
    class Meta:
        model = PoolingTemplate
        fields = ["id", "name", "file", "uploaded_at"]


class LoadFlowcellsTemplateSerializer(ModelSerializer):
    class Meta:
        model = LoadFlowcellsTemplate
        fields = ["id", "name", "file", "uploaded_at"]


class RunStatisticsTemplateSerializer(ModelSerializer):
    class Meta:
        model = RunStatisticsTemplate
        fields = ["id", "name", "file", "uploaded_at"]


class SequencesStatisticsTemplateSerializer(ModelSerializer):
    class Meta:
        model = SequencesStatisticsTemplate
        fields = ["id", "name", "file", "uploaded_at"]
