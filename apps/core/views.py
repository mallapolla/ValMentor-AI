from django.shortcuts import render, redirect

def landing_page(request):
    """Renders the landing page for unauthenticated visitors or redirects to dashboard."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    return render(request, 'landing.html')
