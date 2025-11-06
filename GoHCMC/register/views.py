from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages

# Trang đăng ký
def signup_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "register/signup.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, "register/signup.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, "register/signup.html")

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()
        messages.success(request, "Account created successfully! You can now login.")
        return redirect("login")

    return render(request, "register/signup.html")


# Trang đăng nhập
def custom_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("/")  # hoặc trang chính của bạn
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, "register/login.html")

    return render(request, "register/login.html")
