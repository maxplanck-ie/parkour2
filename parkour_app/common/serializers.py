from rest_framework.serializers import ModelSerializer

from .models import CostUnit


class CostUnitSerializer(ModelSerializer):
    class Meta:
        model = CostUnit
        fields = ('id', 'name')
