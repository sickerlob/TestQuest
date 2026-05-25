from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.conf import settings

class MyUserManager(BaseUserManager):
    def create_user(self, email, name, lastname, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        if not name:
            raise ValueError('Имя обязательно')
        if not lastname:
            raise ValueError('Фамилия обязательна')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            name=name,
            lastname=lastname,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, lastname, password=None, **extra_fields):
        from .models import Role
        try:
            admin_role = Role.objects.filter(role_name__iexact='Admin').first()
            if not admin_role:
                admin_role = Role.objects.get(id=1)
        except Role.DoesNotExist:
            admin_role = Role.objects.create(id=1, role_name='Admin')

        extra_fields.setdefault('role', admin_role)
        return self.create_user(
            email=email,
            name=name,
            lastname=lastname,
            password=password,
            **extra_fields
        )


class Role(models.Model):
    role_name = models.CharField(max_length=50, unique=True, verbose_name="Название роли")

    def __str__(self):
        return self.role_name  # Теперь в выпадающих списках будет видно "Admin", "User" и т.д.

    class Meta:
        db_table = 'roles'
        verbose_name = "Роль"
        verbose_name_plural = "Роли"


class User(AbstractBaseUser):
    name = models.CharField(max_length=50)
    lastname = models.CharField(max_length=50)
    fathername = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='users')
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'lastname']
    objects = MyUserManager()
    @property
    def is_staff(self):
        return self.role and self.role.role_name.lower() == 'admin'
    @property
    def is_superuser(self):
        return self.role and self.role.role_name.lower() == 'admin'
    def has_perm(self, perm, obj=None):
        return self.is_superuser
    def has_module_perms(self, app_label):
        return self.is_superuser
    def has_access(self, element_name, action):
        """
        Проверяет, есть ли у пользователя доступ к определенному действию над элементом.
        element_name: str (например, 'posts')
        action: str (например, 'can_read_all', 'can_create')
        """
        # Если админ — пускаем везде автоматически
        if self.is_superuser:
            return True

        if not self.role:
            return False

        # Импортируем RoleAccess локально внутри функции, чтобы избежать циклической зависимости
        from .models import RoleAccess

        # Ищем запись о правах для текущей роли и нужного элемента управления
        access_rule = RoleAccess.objects.filter(
            role=self.role,
            element__element_name=element_name
        ).first()

        # Если правило существует, динамически забираем значение поля (True/False)
        if access_rule and hasattr(access_rule, action):
            return getattr(access_rule, action)

        return False

    class Meta:
        db_table = 'users'
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class ElementsControl(models.Model):
    element_name = models.CharField(max_length=100, unique=True, verbose_name="Имя контролируемого элемента")

    def __str__(self):
        return self.element_name

    class Meta:
        db_table = 'elements_control'
        verbose_name = "Элемент управления"
        verbose_name_plural = "Элементы управления"


class RoleAccess(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='access_rules', verbose_name="Роль")
    element = models.ForeignKey(ElementsControl, on_delete=models.CASCADE, related_name='rules', verbose_name="Элемент")

    can_create = models.BooleanField(default=False, verbose_name="Cоздание (Create)")
    can_read_all = models.BooleanField(default=False, verbose_name="Чтение всех (Read All)")
    can_read_own = models.BooleanField(default=False, verbose_name="Чтение своих (Read Own)")
    can_update_all = models.BooleanField(default=False, verbose_name="Модификация всех (Update All)")
    can_update_own = models.BooleanField(default=False, verbose_name="Модификация своих (Update Own)")
    can_delete_own = models.BooleanField(default=False, verbose_name="Удаление своих (Delete Own)")
    can_delete_all = models.BooleanField(default=False, verbose_name="Удаление всех (Delete All)")

    def __str__(self):
        return f"Доступ роли {self.role.role_name} к {self.element.element_name}"

    class Meta:
        db_table = 'role_access'
        unique_together = ('role', 'element')
        verbose_name = "Право доступа роли"
        verbose_name_plural = "Права доступа ролей"

class PostFromUser(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Текст поста")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name="Автор"
    )
    # Это поле теперь совпадает с колонкой в MySQL
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        db_table = 'posts_from_users'
        verbose_name = "Пост"
        verbose_name_plural = "Посты"
        ordering = ['-created_at'] # Сортировка по дате: новые сверху

    def __str__(self):
        return self.title