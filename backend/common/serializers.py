from rest_framework.serializers import ModelSerializer
from .models import LibraryPreparationTemplate, PoolingTemplate

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


class LibraryPreparationTemplateSerializer(ModelSerializer):
    class Meta:
        model = LibraryPreparationTemplate
        fields = ["id", "name", "file", "uploaded_at"]


class PoolingTemplateSerializer(ModelSerializer):
    class Meta:
        model = PoolingTemplate
        fields = ["id", "name", "file", "uploaded_at"]
