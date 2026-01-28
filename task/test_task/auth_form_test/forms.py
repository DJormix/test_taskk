
from django import forms
from .models import AppUser
from django.contrib.auth.hashers import make_password
from django import forms
from .models import AppUser
from django.contrib.auth.hashers import check_password


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'example@mail.com',
            'id': 'email'
        }),
        label='Email'
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Введите пароль',
            'id': 'password'
        }),
        label='Пароль'
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            try:

                user = AppUser.objects.get(email=email)


                if not user.isActive:
                    raise forms.ValidationError("Аккаунт деактивирован. Обратитесь к администратору.")

                if not check_password(password, user.password):
                    raise forms.ValidationError("Неверный email или пароль")


                cleaned_data['user'] = user

            except AppUser.DoesNotExist:
                raise forms.ValidationError("Неверный email или пароль")

        return cleaned_data

class UserRegistrationForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'example@mail.com',
            'id': 'id_email'
        }),
        label='Email адрес'
    )

    name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Введите имя',
            'id': 'id_name'
        }),
        label='Имя',
        max_length=100
    )

    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Введите фамилию',
            'id': 'id_last_name'
        }),
        label='Фамилия',
        max_length=100
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Введите пароль',
            'id': 'id_password'
        }),
        label='Пароль',
        min_length=8
    )

    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Повторите пароль',
            'id': 'id_password_confirm'
        }),
        label='Подтверждение пароля'
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')


        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Пароли не совпадают")


        email = cleaned_data.get('email')
        if email and AppUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует")

        return cleaned_data

    def save(self):

        user = AppUser(
            email=self.cleaned_data['email'],
            name=self.cleaned_data['name'],
            last_name=self.cleaned_data['last_name'],
            password=make_password(self.cleaned_data['password']),
            isActive=True,

        )
        user.save()
        return user




class UserUpdateForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'example@mail.com',
            'id': 'id_email'
        }),
        label='Email адрес'
    )

    name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Введите имя',
            'id': 'id_name'
        }),
        label='Имя',
        max_length=100
    )

    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Введите фамилию',
            'id': 'id_last_name'
        }),
        label='Фамилия',
        max_length=100
    )


    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Введите новый пароль',
            'id': 'id_new_password'
        }),
        label='Новый пароль (оставьте пустым, если не хотите менять)',
        required=False,
        min_length=8
    )

    new_password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Повторите новый пароль',
            'id': 'id_new_password_confirm'
        }),
        label='Подтверждение нового пароля',
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:

            self.fields['email'].initial = self.user.email
            self.fields['name'].initial = self.user.name
            self.fields['last_name'].initial = self.user.last_name

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        new_password_confirm = cleaned_data.get('new_password_confirm')


        if new_password or new_password_confirm:
            if new_password != new_password_confirm:
                raise forms.ValidationError("Новые пароли не совпадают")


        email = cleaned_data.get('email')
        if email and self.user and email != self.user.email:
            if AppUser.objects.filter(email=email).exists():
                raise forms.ValidationError("Пользователь с таким email уже существует")

        return cleaned_data

    def save(self):

        if not self.user:
            raise ValueError("Пользователь не указан")


        self.user.email = self.cleaned_data['email']
        self.user.name = self.cleaned_data['name']
        self.user.last_name = self.cleaned_data['last_name']


        new_password = self.cleaned_data.get('new_password')
        if new_password:
            from django.contrib.auth.hashers import make_password
            self.user.password = make_password(new_password)

        self.user.save()
        return self.user