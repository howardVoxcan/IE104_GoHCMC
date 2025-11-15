from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

# -----------------------------
# Trang đăng ký
# -----------------------------
def signup_page(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        errors = []

        # Kiểm tra password match
        if password1 != password2:
            errors.append("Passwords do not match.")

        # Kiểm tra username < 150 ký tự
        if len(username) > 150:
            errors.append("Username must be less than 150 characters.")

        # Kiểm tra username hợp lệ
        import re
        if not re.match(r'^[\w.@+-]+$', username):
            errors.append("Username contains invalid characters. Only letters, digits and @/./+/-/_ are allowed.")

        # Kiểm tra username/email đã tồn tại
        if User.objects.filter(username=username).exists():
            errors.append("Username already exists.")
        if User.objects.filter(email=email).exists():
            errors.append("Email already registered.")

        # Kiểm tra password
        if password1.lower() == username.lower() or password1.lower() == email.lower():
            errors.append("Password cannot be the same as your username or email.")
        if len(password1) < 8:
            errors.append("Password must be at least 8 characters long.")
        if password1.isdigit():
            errors.append("Password cannot be entirely numeric.")

        # Kiểm tra password phổ biến
        common_passwords = ["password", "matkhau", "12345678", "abcdefgh", "abcd1234", "qwerty", "11111111"]
        if password1.lower() in common_passwords:
            errors.append("Password is too common. Please choose a stronger password.")

        # Nếu có lỗi, hiển thị
        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, "register/signup.html", {
                "username": username,
                "email": email,
            })

        # Nếu hợp lệ, tạo user
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()
        messages.success(request, "Account created successfully! You can now login.")
        return redirect("login")

    return render(request, "register/signup.html")


# -----------------------------
# Trang đăng nhập
# -----------------------------
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


# -----------------------------
# Gửi email reset password
# -----------------------------
def send_reset_email(user, request):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    context = {
        'user': user,
        'protocol': 'https' if request.is_secure() else 'http',
        'domain': request.get_host(),
        'uid': uid,
        'token': token,
    }

    subject = "Password Reset - GoHCMC"
    from_email = 'GoHCMC <no-reply@gohcmc.com>'
    to_email = user.email
    html_content = render_to_string("register/password_reset_email.html", context)

    email = EmailMultiAlternatives(subject=subject, body='', from_email=from_email, to=[to_email])
    email.attach_alternative(html_content, "text/html")
    email.send()


# -----------------------------
# Reset mật khẩu qua email (nhập email)
# -----------------------------
def password_reset(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Email invalid.")
            return render(request, "register/password_reset.html")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Account not found with this email.")
            return render(request, "register/password_reset.html")

        send_reset_email(user, request)
        return redirect("password_reset_done")

    return render(request, "register/password_reset.html")


# -----------------------------
# Trang thông báo đã gửi email
# -----------------------------
def password_reset_done(request):
    return render(request, "register/password_reset_done.html")


# -----------------------------
# Xác nhận reset mật khẩu
# -----------------------------
def password_reset_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            password1 = request.POST.get("password1", "")
            password2 = request.POST.get("password2", "")

            errors = []

            # Kiểm tra match
            if password1 != password2:
                errors.append("Passwords do not match.")

            # Kiểm tra độ dài
            if len(password1) < 8:
                errors.append("Password must be at least 8 characters long.")

            # Không được giống username/email
            if password1.lower() == user.username.lower() or password1.lower() == user.email.lower():
                errors.append("Password cannot be the same as your username or email.")

            # Không chỉ toàn số
            if password1.isdigit():
                errors.append("Password cannot be entirely numeric.")

            # Kiểm tra password phổ biến
            common_passwords = ["password", "matkhau", "12345678", "abcdefgh", "abcd1234", "qwerty", "11111111"]
            if password1.lower() in common_passwords:
                errors.append("Password is too common. Please choose a stronger password.")

            # Nếu có lỗi, hiển thị
            if errors:
                for err in errors:
                    messages.error(request, err)
                return render(request, "register/password_reset_confirm.html")

            # Lưu password mới
            user.set_password(password1)
            user.save()
            messages.success(request, "Password reset successfully! You can now login.")
            return redirect("password_reset_complete")

        return render(request, "register/password_reset_confirm.html")

    messages.error(request, "Reset link is invalid or expired.")
    return redirect("password_reset")


# -----------------------------
# Trang thông báo hoàn tất reset
# -----------------------------
def password_reset_complete(request):
    return render(request, "register/password_reset_complete.html")


# -----------------------------
# Logout
# -----------------------------
def logout_view(request):
    logout(request)  # xóa session người dùng
    return redirect('login')
