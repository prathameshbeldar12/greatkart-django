from email import message
from enum import auto
from django.contrib import messages, auth
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from .models import Account
from .forms import RegistrationForm
from django.contrib.auth.decorators import login_required

# verification
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage


from .forms import RegistrationForm
from .models import Account
from django.contrib import messages

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]

            user = Account.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
                password=password
            )
            user.phone_number = phone_number
            user.save()

            # Email Verification
            current_site = get_current_site(request)
            mail_subject = "Activate your PBMart account"
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            send_email = EmailMessage(mail_subject, message, to=[email])
            send_email.send()

        #messages.success(request, "Registration successful! Please check your email to activate your account.")
            return redirect('accounts/login/?command=verification&email='+email)
    else:
        form = RegistrationForm()

    # ✅ Let the template show field-specific errors only (no generic alert here)
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = auth.authenticate(email=email, password=password)

        if user is not None:
            if user.is_active:
                auth.login(request, user)
                messages.success(request, 'Your logged In')
                return redirect('dashboard')
            else:
                messages.warning(request, 'Account is not activated. Please check your email.')
                return redirect('login')
        else:
            messages.warning(request, 'Invalid email or password.')
            return redirect('login')

    return render(request, 'accounts/login.html')


@login_required(login_url='login') 
def logout_view(request):
    auth_logout(request)
    messages.success(request, 'You are logged out.')
    return redirect('login')

from django.utils.encoding import force_str

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account has been activated.")
        return redirect('login')
    else:
        messages.warning(request, "Activation link is invalid or expired.")
        return redirect('register')



#from django.contrib.auth import get_user_model

#def resend_activation_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = get_user_model().objects.get(email=email)
            if not user.is_active:
                current_site = get_current_site(request)
                mail_subject = "Activate your PBMart account (Resend)"
                message = render_to_string('accounts/account_verification_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                })
                send_email = EmailMessage(mail_subject, message, to=[email])
                send_email.send()
                messages.success(request, "Activation link resent. Please check your email.")
            else:
                messages.info(request, "This account is already activated.")
        except Account.DoesNotExist:
            messages.error(request, "No account found with this email.")
        return redirect('resend_activation')

    return render(request, 'accounts/resend_activation.html')


@login_required(login_url='login')
def dashboard(request):
    return render(request, 'accounts/dashboard.html')


from .models import Account  # Or use get_user_model() if you're using a custom user model

def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email=email)

            current_site = get_current_site(request)
            mail_subject = "Reset Your PBMart Password"
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })

            email_message = EmailMessage(mail_subject, message, to=[email])
            email_message.send()

            messages.success(request, 'A password reset link has been sent to your email address.')
            return redirect('login')
        else:
            messages.warning(request, 'Account does not exist.')
            return redirect('forgotPassword')

    return render(request, 'accounts/forgotPassword.html')

def resetpassword_validate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password.')
        return redirect('resetPassword')
    else:
         messages.warning(request, 'This link has been expired.')
         return redirect('login')
    
from django.contrib import messages
from .models import Account

def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            if uid is None:
                messages.error(request, 'Session expired or reset link invalid. Please try again.')
                return redirect('forgotPassword')
            
            try:
                user = Account.objects.get(pk=uid)
            except Account.DoesNotExist:
                messages.error(request, 'User does not exist.')
                return redirect('forgotPassword')

            user.set_password(password)
            user.save()

            # Clear uid from session after use
            request.session.pop('uid', None)

            messages.success(request, 'Password reset successful. Please log in.')
            return redirect('login')
        else:
            messages.warning(request, 'Passwords do not match.')
            return redirect('resetPassword')
    else:
        return render(request, 'accounts/resetPassword.html')
