from django.http import HttpResponseForbidden
from functools import wraps


def check_access(element_name, action):
    """
    Декоратор для проверки прав доступа пользователя к определенному элементу системы.
    Использование: @check_access('posts', 'can_create')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # 1. Проверяем, авторизован ли пользователь вообще
            if not request.user.is_authenticated:
                return HttpResponseForbidden(
                    "<h1>403 Доступ запрещен</h1><p>Вам необходимо авторизоваться в системе.</p>")

            # 2. Вызываем метод, который мы только что добавили в модель User
            if request.user.has_access(element_name, action):
                return view_func(request, *args, **kwargs)

            # 3. Если проверка не прошла — отдаем ошибку 403
            return HttpResponseForbidden(
                "<h1>403 Доступ запрещен</h1><p>У вашей роли недостаточно прав для выполнения этого действия.</p>")

        return _wrapped_view

    return decorator