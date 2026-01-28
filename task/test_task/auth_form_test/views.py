from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .forms import UserRegistrationForm, LoginForm, UserUpdateForm
from .models import AppUser, Role, BusinessElement, AccessRule
from django.views.decorators.http import require_POST
import jwt
import datetime
from django.conf import settings

def index(request):
    return render(request, 'auth_form_test/index.html')

def about(request):
    return render(request, 'auth_form_test/register.html')

def api_demo(request):
    return render(request, 'auth_form_test/api_demo.html')

def dashboard1(request):
    if 'user_id' not in request.session:
        messages.error(request, 'Пожалуйста, войдите в систему')
        return redirect('login')
    user_id = request.session.get('user_id')
    try:
        user = AppUser.objects.get(id=user_id)
        if not user.isActive:
            request.session.flush()
            messages.error(request, 'Ваш аккаунт деактивирован')
            return redirect('login')
    except AppUser.DoesNotExist:
        messages.error(request, 'Пользователь не найден')
        return redirect('login')
    return render(request, 'auth_form_test/dahboard.html', {
        'user': user
    })

def login_view(request):
    if 'user_id' in request.session:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            if not user.isActive:
                messages.error(request, 'Ваш аккаунт деактивирован. Обратитесь к администратору.')
                return render(request, 'auth_form_test/login.html', {'form': form})
            request.session['user_id'] = str(user.id)
            request.session['user_email'] = user.email
            request.session['user_name'] = user.name
            try:
                token = user.generate_jwt_token()
            except Exception as e:
                print(f"Ошибка генерации JWT: {e}")
                token = f"session-{user.id}"
            messages.success(request, f'Добро пожаловать, {user.name}!')
            is_api_request = request.headers.get('Content-Type') == 'application/json'
            if is_api_request:
                return JsonResponse({
                    'success': True,
                    'message': 'Вход выполнен успешно',
                    'token': token,
                    'user': {
                        'id': str(user.id),
                        'email': user.email,
                        'name': user.name,
                        'last_name': user.last_name,
                        'role': user.role.name if user.role else None
                    }
                })
            else:
                response = redirect('dashboard')
                response.set_cookie('auth_token', token, httponly=False,
                                    max_age=7 * 24 * 60 * 60)
                request.session['jwt_token'] = token
                return response
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f'{error}')
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'errors': error_messages
                }, status=400)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = LoginForm()
    return render(request, 'auth_form_test/login.html', {'form': form})

def logout_view(request):
    request.session.flush()
    if request.headers.get('Content-Type') == 'application/json':
        response = JsonResponse({
            'success': True,
            'message': 'Вы успешно вышли из системы'
        })
    else:
        messages.success(request, 'Вы успешно вышли из системы')
        response = redirect('index')
    response.delete_cookie('auth_token')
    response.delete_cookie('sessionid')
    return response

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(
                    request,
                    f'✅ Пользователь {user.name} {user.last_name} успешно зарегистрирован!'
                )
                return redirect('index')
            except Exception as e:
                messages.error(request, f'❌ Ошибка при сохранении: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = UserRegistrationForm()
    return render(request, 'auth_form_test/register.html', {'form': form})

def update_profile(request):
    if 'user_id' not in request.session:
        messages.error(request, 'Пожалуйста, войдите в систему')
        return redirect('login')
    user_id = request.session.get('user_id')
    try:
        user = AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        messages.error(request, 'Пользователь не найден')
        return redirect('login')
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, user=user)
        if form.is_valid():
            try:
                updated_user = form.save()
                request.session['user_email'] = updated_user.email
                request.session['user_name'] = updated_user.name
                messages.success(
                    request,
                    '✅ Ваши данные успешно обновлены!'
                )
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f'❌ Ошибка при сохранении: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = UserUpdateForm(user=user)
    return render(request, 'auth_form_test/change_user_data.html', {
        'form': form,
        'user': user
    })

def deactivate_account(request):
    if 'user_id' not in request.session:
        messages.error(request, 'Пожалуйста, войдите в систему')
        return redirect('login')
    if request.method == 'POST':
        try:
            user_id = request.session.get('user_id')
            user_obj = AppUser.objects.get(id=user_id)
            if not user_obj.isActive:
                messages.warning(request, 'Аккаунт уже деактивирован')
                request.session.flush()
                return redirect('login')
            user_obj.isActive = False
            user_obj.save()
            request.session.flush()
            messages.success(request, 'Ваш аккаунт был успешно деактивирован')
            return redirect('login')
        except AppUser.DoesNotExist:
            messages.error(request, 'Пользователь не найден')
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f'Произошла ошибка: {str(e)}')
            return redirect('dashboard')
    return redirect('dashboard')