from rest_framework.serializers import ModelSerializer

from .models import CostUnit, User


class CostUnitSerializer(ModelSerializer):
    class Meta:
        model = CostUnit
        fields = ("id", "name")


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("email",)
