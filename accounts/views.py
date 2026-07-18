from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f"Hisob yaratildi! {username}, tizimga kirishingiz mumkin.")
            return redirect('login')  # Ro'yxatdan o'tgach Login sahifasiga yuboradi
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})