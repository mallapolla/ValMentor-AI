from rest_framework import serializers
from .models import Resume

class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'file', 'status', 'ats_score', 'missing_skills', 'suggestions', 'job_matches', 'created_at']
        read_only_fields = ['id', 'status', 'ats_score', 'missing_skills', 'suggestions', 'job_matches', 'created_at']
