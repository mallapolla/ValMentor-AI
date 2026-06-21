from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, UserProfile

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'username')

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('email', 'username', 'is_active', 'is_staff')

class UserProfileForm(forms.ModelForm):
    skills_raw = forms.CharField(
        label="Skills (comma separated)",
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Django, Python, REST APIs, Valkey',
            'class': 'w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-100 focus:outline-none focus:border-cyan-500'
        })
    )
    
    interests_raw = forms.CharField(
        label="Career Interests (comma separated)",
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Backend Engineering, AI Agents, System Design',
            'class': 'w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-100 focus:outline-none focus:border-cyan-500'
        })
    )

    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio', 'current_role', 'target_role', 'experience_level']
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-100 focus:outline-none focus:border-cyan-500'
            }),
            'current_role': forms.TextInput(attrs={
                'class': 'w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-100 focus:outline-none focus:border-cyan-500'
            }),
            'target_role': forms.TextInput(attrs={
                'class': 'w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-100 focus:outline-none focus:border-cyan-500'
            }),
            'experience_level': forms.Select(attrs={
                'class': 'w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-100 focus:outline-none focus:border-cyan-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['skills_raw'].initial = ", ".join(self.instance.skills or [])
            self.fields['interests_raw'].initial = ", ".join(self.instance.career_interests or [])

    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # Parse comma separated skills & interests
        skills_str = self.cleaned_data.get('skills_raw', '')
        profile.skills = [s.strip() for s in skills_str.split(',') if s.strip()]
        
        interests_str = self.cleaned_data.get('interests_raw', '')
        profile.career_interests = [i.strip() for i in interests_str.split(',') if i.strip()]
        
        if commit:
            profile.save()
        return profile
