from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import SerializerMethodField


from .models import CostUnit, User


class CostUnitSerializer(ModelSerializer):
    class Meta:
        model = CostUnit
        fields = ("id", "name")


class PrincipalInvestigatorSerializer(ModelSerializer):
    name = SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "name")

    def get_name(self, obj):
        return  str(obj)