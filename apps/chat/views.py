from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from services.memory_flow import MemoryFlowOrchestrator

# ──────────────────────────────────────────────────────────
# Django Template Views (HTMX compatible)
# ──────────────────────────────────────────────────────────

@login_required
def chat_home(request):
    """Renders the main chat workspace listing past conversations."""
    conversations = Conversation.objects.filter(user=request.user)
    active_conv_id = request.GET.get('c')
    
    active_conv = None
    messages_list = []
    if active_conv_id:
        active_conv = get_object_or_404(Conversation, id=active_conv_id, user=request.user)
        messages_list = active_conv.messages.all()
    elif conversations.exists():
        # Fallback to most recent conversation
        active_conv = conversations.first()
        messages_list = active_conv.messages.all()

    # Recommended Suggested Prompts
    suggested_prompts = [
        "What skills do I need to become a Django backend developer?",
        "Can you ask me some Python data structures interview questions?",
        "How can I improve my resume's ATS match percentage?",
        "Give me a study guide for PostgreSQL performance tuning."
    ]

    return render(request, 'chat/chat.html', {
        'conversations': conversations,
        'active_conversation': active_conv,
        'messages_list': messages_list,
        'suggested_prompts': suggested_prompts
    })

@login_required
def create_conversation(request):
    """Creates a new conversation thread and redirects."""
    category = request.GET.get('category', 'General Career')
    title = f"Mentor Session: {category}"
    conv = Conversation.objects.create(user=request.user, title=title, category=category)
    return redirect(f"{reverse_url('chat:home')}?c={conv.id}")

@login_required
def send_message(request, conversation_id):
    """Handles messages posted via HTMX, streams response, and updates chat DOM."""
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    user_query = request.POST.get('message', '').strip()
    
    if not user_query:
        return HttpResponse(status=204)

    # 1. Save user message in DB
    user_msg = Message.objects.create(conversation=conversation, role='user', content=user_query)
    
    # 2. Invoke memory orchestrator to run LLM agent
    orchestrator = MemoryFlowOrchestrator()
    response_text = orchestrator.process_user_query(request.user, user_query)
    
    # 3. Save assistant message in DB
    assistant_msg = Message.objects.create(conversation=conversation, role='assistant', content=response_text)

    # Update conversation modification time
    conversation.save()

    # Renders the message partials to update HTMX view
    return render(request, 'chat/partials/message_pair.html', {
        'user_message': user_msg,
        'assistant_message': assistant_msg
    })

# Helper helper to safely resolve URLs
def reverse_url(view_name):
    from django.urls import reverse
    return reverse(view_name)


# ──────────────────────────────────────────────────────────
# Django REST API Views (for external clients)
# ──────────────────────────────────────────────────────────

class APIConversationListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        convs = Conversation.objects.filter(user=request.user)
        serializer = ConversationSerializer(convs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ConversationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class APIMessageSendView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
        query = request.data.get('message', '').strip()
        if not query:
            return Response({'error': 'Message content cannot be blank'}, status=status.HTTP_400_BAD_REQUEST)

        # Process user query
        user_msg = Message.objects.create(conversation=conversation, role='user', content=query)
        
        orchestrator = MemoryFlowOrchestrator()
        response_text = orchestrator.process_user_query(request.user, query)
        
        assistant_msg = Message.objects.create(conversation=conversation, role='assistant', content=response_text)
        conversation.save()

        return Response({
            'user_message': MessageSerializer(user_msg).data,
            'assistant_message': MessageSerializer(assistant_msg).data
        }, status=status.HTTP_201_CREATED)
