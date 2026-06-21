import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, UserProfile
from .forms import CustomUserCreationForm, UserProfileForm
from .serializers import UserSerializer

# ──────────────────────────────────────────────────────────
# Django Template Views
# ──────────────────────────────────────────────────────────

def register_view(request):
    """Handles HTML user registration."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True  # Keep active in development
            user.verification_token = str(uuid.uuid4())
            user.save()
            
            # Send verification link (mocked in console)
            verify_url = request.build_absolute_uri(
                reverse('accounts:verify_email', kwargs={'token': user.verification_token})
            )
            send_mail(
                subject='Verify your ValMentor AI Account',
                message=f'Welcome! Click here to verify your account: {verify_url}',
                from_email='noreply@valmentor.ai',
                recipient_list=[user.email],
                fail_silently=True
            )
            
            messages.success(request, 'Registration successful! Verification email sent (check terminal console).')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Error during registration. Please verify form values.')
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    """Handles HTML user logins."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard:home')
        else:
            messages.error(request, 'Invalid email or password.')
            
    return render(request, 'accounts/login.html')

def logout_view(request):
    """Handles logouts."""
    logout(request)
    messages.info(request, 'Logged out successfully.')
    return redirect('core:landing')

def verify_email_view(request, token):
    """Validates email verification tokens."""
    user = get_object_or_404(User, verification_token=token)
    user.is_email_verified = True
    user.verification_token = None
    user.save()
    messages.success(request, 'Email verified successfully! You can now log in.')
    return redirect('accounts:login')

@login_required
def profile_view(request):
    """View and update current user's profile."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = UserProfileForm(instance=profile)
        
    return render(request, 'accounts/profile.html', {'form': form, 'profile': profile})

def forgot_password_view(request):
    """Forgot password request view."""
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            # Mock reset link
            messages.success(request, 'Password reset instructions sent (check console).')
        else:
            messages.error(request, 'No user found with that email.')
    return render(request, 'accounts/forgot_password.html')


# ──────────────────────────────────────────────────────────
# Django REST API Views (for external clients / JWT authentication)
# ──────────────────────────────────────────────────────────

class APIRegisterView(APIView):
    """API endpoint for JWT-based user registration."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            # Create user
            user = User.objects.create_user(
                username=request.data.get('username'),
                email=request.data.get('email'),
                password=request.data.get('password')
            )
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class APIUserProfileView(APIView):
    """API endpoint to get or update user profiles via JWT."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        return Response(UserSerializer(request.user).data)

    def put(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        # Parse fields
        profile.bio = request.data.get('bio', profile.bio)
        profile.current_role = request.data.get('current_role', profile.current_role)
        profile.target_role = request.data.get('target_role', profile.target_role)
        profile.experience_level = request.data.get('experience_level', profile.experience_level)
        profile.skills = request.data.get('skills', profile.skills)
        profile.career_interests = request.data.get('career_interests', profile.career_interests)
        profile.save()
        return Response(UserSerializer(request.user).data)
