from rest_framework import serializers
from .models import InterviewSession, InterviewQuestion

class InterviewQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewQuestion
        fields = ['id', 'question_text', 'user_answer', 'ai_feedback', 'score']

class InterviewSessionSerializer(serializers.ModelSerializer):
    questions = InterviewQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = InterviewSession
        fields = ['id', 'category', 'difficulty', 'is_completed', 'score', 'weak_areas', 'feedback', 'questions', 'created_at']
        read_only_fields = ['id', 'is_completed', 'score', 'weak_areas', 'feedback', 'created_at']
