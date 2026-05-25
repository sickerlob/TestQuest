from django.contrib.auth import authenticate, login, logout
from .forms import RegistrationForm, LoginForm
from .decorators import check_access
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .models import User, Role
from django.shortcuts import render, redirect
from .models import PostFromUser
from django.db.models import Q
from django.shortcuts import render, get_object_or_404

@login_required
def post_detail_view(request, post_id):
    # Достаем конкретный пост по ID или отдаем 404, если такого ID нет в базе
    post = get_object_or_404(PostFromUser, id=post_id)
    return render(request, 'forum/post_detail.html', {'post': post})

@check_access('posts', 'can_create')
def create_post_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')

        if title and content:
            # Создаем запись напрямую в MySQL таблицу posts_from_users
            PostFromUser.objects.create(
                title=title,
                content=content,
                owner=request.user  # Передаем текущего авторизованного юзера
            )
            # После успешного сохранения перенаправляем на главную страницу форума
            return redirect('forum_home')

    return render(request, 'forum/create_post.html')

def guest_login_view(request):
    # 1. Находим дефолтную роль для гостя (например, 'User')
    user_role = Role.objects.filter(role_name='User').first()
    if not user_role:
        # Если ролей еще нет, берем самую первую доступную
        user_role = Role.objects.first()

    # 2. Получаем или автоматически создаем гостевой аккаунт в БД
    guest_user, created = User.objects.get_or_create(
        email='guest@forum.local',
        defaults={
            'name': 'Гость',
            'lastname': 'Анонимный',
            'role': user_role,
            'is_active': True
        }
    )

    if created:
        guest_user.set_password('GuestPassword123!')
        guest_user.save()

    login(request, guest_user)

    # 4. Перенаправляем на главную страницу форума
    return redirect('forum_home')


@login_required  # или твой @check_access, если настраивал права для профиля
def profile_view(request):
    # Получаем из базы только посты текущего пользователя
    user_posts = PostFromUser.objects.filter(owner=request.user)

    context = {
        'user_posts': user_posts,
        # Количество постов, чтобы вывести красивую статистику
        'posts_count': user_posts.count()
    }
    return render(request, 'forum/profile.html', context)



@check_access('posts', 'can_read_all')
def forum_home_view(request):
    # Получаем поисковые запросы из формы (атрибуты name="search_topic" и name="search_tag")
    search_topic = request.GET.get('search_topic', '').strip()
    search_tag = request.GET.get('search_tag', '').strip()

    # Изначально берем все посты
    posts = PostFromUser.objects.all()

    # Если пользователь ввел что-то в поиск по темам
    if search_topic:
        # Фильтруем: ищем совпадения без учета регистра в заголовке ИЛИ в тексте поста
        posts = posts.filter(
            Q(title__icontains=search_topic) | Q(content__icontains=search_topic)
        )

    # Если пользователь ввел хештег (например, "it" или "#it")
    if search_tag:
        # Убираем символ #, если пользователь его ввел, чтобы искать чистый текст
        clean_tag = search_tag.replace('#', '')
        # Здесь логика зависит от того, как у тебя хранятся теги.
        # Если это просто текст в поле контента, ищем по контенту:
        posts = posts.filter(content__icontains=f"#{clean_tag}")

    context = {
        'posts': posts,
        'search_topic': search_topic,  # Возвращаем в поле ввода, чтобы текст не пропадал
        'search_tag': search_tag,
    }
    return render(request, 'forum/home.html', context)

def register_view(request):
    if request.user.is_authenticated:
        return redirect('forum_home')
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            # Находим дефолтную роль 'User' для обычного пользователя
            try:
                user_role = Role.objects.filter(role_name__iexact='User').first()
                if not user_role:
                    user_role = Role.objects.get(id=2)  # Или по ID, если создал вторую роль
            except Role.DoesNotExist:
                # Если вдруг роли 'User' еще нет в БД, создадим её на лету
                user_role = Role.objects.create(id=2, role_name='User')

            # Создаем пользователя через наш MyUserManager (он сам захэширует пароль)
            user = User.objects.create_user(
                email=data['email'],
                name=data['name'],
                lastname=data['lastname'],
                fathername=data.get('fathername'),
                password=data['password'],
                role=user_role  # Принудительно задаем роль пользователя
            )

            # Сразу авторизуем пользователя после успешной регистрации

            return redirect('login')
    else:
        form = RegistrationForm()

    return render(request, 'forum/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('forum_home')

    error_message = None
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Django вызовет наш бэкенд авторизации, сверит email и хэш пароля
            user = authenticate(request, username=email, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('forum_home')
                else:
                    error_message = "Аккаунт заблокирован."
            else:
                error_message = "Неверный Email или пароль."
    else:
        form = LoginForm()

    return render(request, 'forum/login.html', {'form': form, 'error_message': error_message})


def logout_view(request):
    logout(request)
    return redirect('login')