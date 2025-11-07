from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import logout

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

# Reset mật khẩu qua email
def password_reset(request):
    context = {}
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            # Tạo token reset password
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = request.build_absolute_uri(f"/reset/{uid}/{token}/")

            # Gửi email
            subject = "Password Reset for GoHCMC"
            message = render_to_string("password_reset_email.html", {
                "user": user,
                "reset_link": reset_link
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

            context["success"] = "Email đã được gửi. Vui lòng kiểm tra hộp thư đến."
        except User.DoesNotExist:
            context["error"] = "Email không tồn tại trong hệ thống."
    return render(request, "password_reset.html", context)

def logout_view(request):
    logout(request)  # xóa session người dùng
    return redirect('login')  # sau khi logout, chuyển về trang login