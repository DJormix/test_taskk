# auth_form_test/models.py
from django.db import models
from django.utils import timezone
import uuid
import jwt
import datetime
from django.conf import settings


class Role(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True, verbose_name='Название роли')
    description = models.TextField(verbose_name='Описание роли', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'
        ordering = ['name']

    def __str__(self):
        return self.name


class BusinessElement(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, verbose_name='Название объекта')
    code = models.CharField(max_length=50, unique=True, verbose_name='Код объекта')
    description = models.TextField(verbose_name='Описание', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Бизнес-объект'
        verbose_name_plural = 'Бизнес-объекты'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class AccessRule(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name='Роль')
    element = models.ForeignKey(BusinessElement, on_delete=models.CASCADE, verbose_name='Бизнес-объект')


    can_read = models.BooleanField(default=False, verbose_name='Может просматривать')
    can_create = models.BooleanField(default=False, verbose_name='Может создавать')
    can_update = models.BooleanField(default=False, verbose_name='Может обновлять')
    can_delete = models.BooleanField(default=False, verbose_name='Может удалять')


    can_read_all = models.BooleanField(default=False, verbose_name='Может просматривать все')
    can_update_all = models.BooleanField(default=False, verbose_name='Может обновлять все')
    can_delete_all = models.BooleanField(default=False, verbose_name='Может удалять все')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Правило доступа'
        verbose_name_plural = 'Правила доступа'
        unique_together = ['role', 'element']
        ordering = ['role', 'element']

    def __str__(self):
        return f"{self.role.name} -> {self.element.name}"



class AppUser(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='ID'
    )
    email = models.EmailField(
        unique=True,
        verbose_name='Email',
        max_length=255
    )
    name = models.CharField(
        verbose_name='Имя',
        max_length=100
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=100
    )
    password = models.CharField(
        verbose_name='Пароль',
        max_length=255
    )
    isActive = models.BooleanField(
        verbose_name='Активен',
        default=True
    )
    date_reg = models.DateTimeField(
        verbose_name='Дата регистрации',
        default=timezone.now
    )

    # Новое поле для роли
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Роль пользователя'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-date_reg']
        db_table = 'users'

    def __str__(self):
        return f"{self.email} ({self.name} {self.last_name})"

    def generate_jwt_token(self):

        payload = {
            'user_id': str(self.id),
            'email': self.email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
            'iat': datetime.datetime.utcnow()
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        if isinstance(token, bytes):
            token = token.decode('utf-8')
        return token

    def check_permission(self, element_code, permission_type):

        if not self.role or not self.isActive:
            return False

        try:
            element = BusinessElement.objects.get(code=element_code)
            rule = AccessRule.objects.get(role=self.role, element=element)

            if permission_type == 'read':
                return rule.can_read
            elif permission_type == 'create':
                return rule.can_create
            elif permission_type == 'update':
                return rule.can_update
            elif permission_type == 'delete':
                return rule.can_delete
            elif permission_type == 'read_all':
                return rule.can_read_all
            elif permission_type == 'update_all':
                return rule.can_update_all
            elif permission_type == 'delete_all':
                return rule.can_delete_all
            else:
                return False
        except (BusinessElement.DoesNotExist, AccessRule.DoesNotExist):
            return False