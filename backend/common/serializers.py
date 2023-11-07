from rest_framework.serializers import ModelSerializer

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
