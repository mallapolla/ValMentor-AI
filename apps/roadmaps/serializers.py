from rest_framework import serializers
from .models import Roadmap, UserRoadmap

class RoadmapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roadmap
        fields = ['id', 'title', 'slug', 'category', 'description', 'difficulty', 'estimated_weeks', 'milestones']

class UserRoadmapSerializer(serializers.ModelSerializer):
    roadmap = RoadmapSerializer(read_only=True)

    class Meta:
        model = UserRoadmap
        fields = ['id', 'roadmap', 'progress_pct', 'completed_milestones', 'started_at']
