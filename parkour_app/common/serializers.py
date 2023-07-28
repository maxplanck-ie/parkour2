from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import SerializerMethodField


from .models import CostUnit, User, Organization


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


class BioinformaticianSerializer(ModelSerializer):
    name = SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "name")

    def get_name(self, obj):
        return str(obj)


class StaffMemberSerializer(ModelSerializer):
    name = SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "name")

    def get_name(self, obj):
        return str(obj)


class OrganizationSerializer(ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name")


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("email",)
