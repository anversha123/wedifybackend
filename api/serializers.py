from rest_framework import serializers
from .models import Planner, BookingRequest

class PlannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Planner
        fields = '__all__'

class BookingRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingRequest
        fields = '__all__'
