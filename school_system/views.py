from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import UserProfile
from organization.forms import CampusForm
from organization.models import Campus


def get_user_profile(user):
    return getattr(user, 'profile', None)


def get_campus_manager_campus(user):
    profile = get_user_profile(user)
    if profile is not None and profile.campus is not None:
        return profile.campus
    return Campus.objects.filter(manager=user, is_active=True).order_by('name').first()


def principal_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = get_user_profile(request.user)
        if profile is None or profile.role != UserProfile.ROLE_PRINCIPAL:
            return HttpResponseForbidden('无权限访问此页面')
        return view_func(request, *args, **kwargs)

    return wrapper


def login_view(request):
    error_message = ''

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/dashboard/')

        error_message = '登录失败：用户名或密码错误，请重试'

    return render(request, 'accounts/login.html', {'error_message': error_message})


def logout_view(request):
    logout(request)
    return redirect('/login/')


@login_required
def dashboard_view(request):
    profile = get_user_profile(request.user)
    role_display = '未设置'
    campus_display = '未设置'
    dashboard_mode = 'unset'
    active_campuses = Campus.objects.none()
    selected_campus = None
    manager_campus = None

    if profile is not None:
        role_display = profile.get_role_display()
        if profile.role == profile.ROLE_PRINCIPAL:
            dashboard_mode = 'principal'
            active_campuses = Campus.objects.filter(is_active=True).order_by('name')
            if request.GET.get('scope') == 'all':
                request.session.pop('current_campus_id', None)
            selected_campus_id = request.session.get('current_campus_id')
            if selected_campus_id is not None:
                selected_campus = active_campuses.filter(pk=selected_campus_id).first()
            campus_display = selected_campus.name if selected_campus else '全部校区'
        elif profile.role == profile.ROLE_CAMPUS_MANAGER:
            dashboard_mode = 'campus_manager'
            manager_campus = get_campus_manager_campus(request.user)
            campus_display = manager_campus.name if manager_campus else '未设置'
        elif profile.role == profile.ROLE_TEACHER:
            dashboard_mode = 'teacher'
            campus_display = profile.campus.name if profile.campus is not None else '未设置'

    return render(
        request,
        'accounts/dashboard.html',
        {
            'role_display': role_display,
            'campus_display': campus_display,
            'dashboard_mode': dashboard_mode,
            'active_campuses': active_campuses,
            'selected_campus': selected_campus,
            'manager_campus': manager_campus,
        },
    )


@login_required
def campus_workbench_view(request, campus_id):
    campus = get_object_or_404(Campus, pk=campus_id)
    profile = get_user_profile(request.user)

    if profile is None:
        return HttpResponseForbidden('无权限访问此页面')

    if profile.role == UserProfile.ROLE_PRINCIPAL:
        request.session['current_campus_id'] = campus.pk
    elif profile.role == UserProfile.ROLE_CAMPUS_MANAGER:
        manager_campus = get_campus_manager_campus(request.user)
        if manager_campus is None or manager_campus.pk != campus.pk:
            return HttpResponseForbidden('无权限访问此页面')
    else:
        return HttpResponseForbidden('无权限访问此页面')

    return render(request, 'organization/campus_workbench.html', {'campus': campus})


@principal_required
def campus_list_view(request):
    campuses = Campus.objects.select_related('manager').order_by('name')
    return render(request, 'organization/campus_list.html', {'campuses': campuses})


@principal_required
def campus_create_view(request):
    if request.method == 'POST':
        form = CampusForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/dashboard/campuses/')
    else:
        form = CampusForm()

    return render(
        request,
        'organization/campus_form.html',
        {
            'form': form,
            'page_title': '系统设置：新建校区',
            'submit_text': '保存校区',
        },
    )


@principal_required
def campus_edit_view(request, pk):
    campus = get_object_or_404(Campus, pk=pk)

    if request.method == 'POST':
        form = CampusForm(request.POST, instance=campus)
        if form.is_valid():
            form.save()
            return redirect('/dashboard/campuses/')
    else:
        form = CampusForm(instance=campus)

    return render(
        request,
        'organization/campus_form.html',
        {
            'form': form,
            'page_title': '系统设置：编辑校区',
            'submit_text': '保存修改',
        },
    )
