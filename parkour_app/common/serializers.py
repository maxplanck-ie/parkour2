from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import SerializerMethodField


from .models import CostUnit, PrincipalInvestigator


class CostUnitSerializer(ModelSerializer):
    class Meta:
        model = CostUnit
        fields = ("id", "name")


class PrincipalInvestigatorSerializer(ModelSerializer):
    name = SerializerMethodField()

    class Meta:
        model = PrincipalInvestigator
        fields = ("id", "name")

    def get_name(self, obj):
        return str(obj)