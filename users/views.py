# users/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from django.db import transaction
from .models import (
    User,
    Administrator,
    OperationLog,
    Teacher,
    APIKey,
    Course,
    Student,
    StudentCourse,
    Question,
    StudentAnswer,
    ScoringFeedback,
)
from .forms import (
    AddTeacherForm,
    AddStudentForm,
    EditTeacherForm,
    EditStudentForm,
    AddAPIKeyForm,
    EditAPIKeyForm,
    CourseForm,
    QuestionForm,
    SubmitAnswerForm,
    GradeAnswerForm,
    EditPromptForm,
    AddQuestionForm,
)
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from functools import wraps

import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .services.judge_gpt import get_judge_from_gpt
from .services.judge_qwen import get_judge_from_qwen

# =====================
# 公共视图
# =====================


# 首页视图
def home(request):
    return render(request, "home.html")


# 注册视图
def register(request):
    if request.method == "POST":
        role = request.POST.get("role")
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if role == "teacher":
            if Teacher.objects.filter(Email=email).exists():
                messages.error(request, "教师邮箱已存在")
                return redirect("register")
            teacher = Teacher.objects.create(
                Name=name, Email=email, Password=make_password(password)
            )
            messages.success(
                request, f"注册成功！您的教师ID为 {teacher.TeacherID}，请妥善保存！"
            )
            return redirect("login")

        elif role == "student":
            if Student.objects.filter(Email=email).exists():
                messages.error(request, "学生邮箱已存在")
                return redirect("register")
            student = Student.objects.create(
                Name=name, Email=email, Password=make_password(password)
            )
            messages.success(
                request, f"注册成功！您的学生ID为 {student.StudentID}，请妥善保存！"
            )
            return redirect("login")

        else:
            messages.error(request, "无效的用户角色")
            return redirect("register")

    return render(request, "register.html")


# 登录视图
def login_view(request):
    if request.method == "POST":
        role = request.POST.get("role")
        email = request.POST.get("email")
        password = request.POST.get("password")

        # 清除所有会话变量
        for key in ["admin_id", "teacher_id", "student_id"]:
            if key in request.session:
                del request.session[key]

        if role == "admin":
            try:
                admin = Administrator.objects.get(Email=email)
                if (
                    admin
                    and admin.Password
                    and check_password(password, admin.Password)
                ):
                    request.session["admin_id"] = admin.AdminID
                    return redirect("admin_dashboard")
                else:
                    messages.error(request, "邮箱或密码错误，请重新输入")
            except Administrator.DoesNotExist:
                messages.error(request, "邮箱或密码错误，请重新输入")

        elif role == "teacher":
            try:
                teacher = Teacher.objects.get(Email=email)
                if (
                    teacher
                    and teacher.Password
                    and check_password(password, teacher.Password)
                ):
                    request.session["teacher_id"] = teacher.TeacherID
                    return redirect("teacher_dashboard")
                else:
                    messages.error(request, "邮箱或密码错误，请重新输入")
            except Teacher.DoesNotExist:
                messages.error(request, "邮箱或密码错误，请重新输入")

        elif role == "student":
            try:
                student = Student.objects.get(Email=email)
                if (
                    student
                    and student.Password
                    and check_password(password, student.Password)
                ):
                    request.session["student_id"] = student.StudentID
                    return redirect("student_dashboard")
                else:
                    messages.error(request, "邮箱或密码错误，请重新输入")
            except Student.DoesNotExist:
                messages.error(request, "邮箱或密码错误，请重新输入")

        else:
            messages.error(request, "无效的登录类型")

    return render(request, "login.html")


# 登出视图
def logout_view(request):
    # 清除自定义会话
    for key in ["admin_id", "teacher_id", "student_id"]:
        if key in request.session:
            del request.session[key]
    request.session.flush()
    messages.success(request, "成功登出")
    return redirect("home")


# =====================
# 用户主页
# =====================


# 教师主页
def teacher_dashboard(request):
    teacher_id = request.session.get("teacher_id")
    if not teacher_id:
        messages.error(request, "无权限访问教师主页")
        return redirect("login")

    teacher = Teacher.objects.get(TeacherID=request.session["teacher_id"])
    courses = Course.objects.filter(TeacherID=teacher)

    context = {
        "teacher": teacher,
        "courses": courses,
    }
    return render(request, "teacher_dashboard.html", context)


# 学生主页
def student_dashboard(request):
    student_id = request.session.get("student_id")
    if not student_id:
        messages.error(request, "无权限访问学生主页")
        return redirect("login")

    student = Student.objects.get(StudentID=request.session["student_id"])
    enrolled_courses = StudentCourse.objects.filter(StudentID=student)

    context = {
        "student": student,
        "enrolled_courses": enrolled_courses,
    }
    return render(request, "student_dashboard.html", context)


# 管理员主页
def admin_dashboard(request):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        messages.error(request, "无权限访问管理员主页")
        return redirect("login")

    admin = get_object_or_404(Administrator, AdminID=admin_id)
    teachers = Teacher.objects.all()
    students = Student.objects.all()
    questions = Question.objects.all().order_by("-CreatedAt")  # 新增试题列表

    context = {
        "admin": admin,
        "teachers": teachers,
        "students": students,
        "questions": questions,
    }
    return render(request, "admin_dashboard.html", context)


# =====================
# 管理员相关视图
# =====================
# 以下视图需要管理员权限访问


# 添加教师视图
def add_teacher(request):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    if request.method == "POST":
        form = AddTeacherForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    teacher = form.save()
                    messages.success(request, f"成功添加教师：{teacher.Name}")
                    OperationLog.objects.create(
                        AdminID=get_object_or_404(Administrator, AdminID=admin_id),
                        Operation="新增教师",
                        Details=f"新增教师：{teacher.Name}，邮箱：{teacher.Email}，密码：{teacher.Password}",
                        Timestamp=timezone.now(),
                    )
                return redirect("admin_dashboard")
            except Exception as e:
                messages.error(request, "添加教师失败，请检查输入内容。")

    else:
        form = AddTeacherForm()

    return render(request, "add_teacher.html", {"form": form})


# 编辑教师信息视图
def edit_teacher(request, teacher_id):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    teacher = get_object_or_404(Teacher, TeacherID=teacher_id)

    if request.method == "POST":
        form = EditTeacherForm(request.POST, instance=teacher)
        if form.is_valid():
            try:
                with transaction.atomic():  # 确保修改和操作日志记录为原子操作
                    old_name = teacher.Name
                    old_email = teacher.Email
                    old_pw = teacher.Password
                    form.save()  # 保存修改
                    # form.cleaned_data是一个字典，包含了表单中所有字段的值
                    new_name = form.cleaned_data.get("Name")
                    new_email = form.cleaned_data.get("Email")
                    new_pw = form.cleaned_data.get("Password")
                    OperationLog.objects.create(
                        AdminID=get_object_or_404(Administrator, AdminID=admin_id),
                        Operation="编辑教师信息",
                        Details=f'编辑教师ID {teacher.TeacherID}：从姓名 "{old_name}" 、邮箱 "{old_email}"、密码 "{old_pw}" 修改为姓名 "{new_name}" 、邮箱 "{new_email}、密码 "{new_pw}"',
                        Timestamp=timezone.now(),
                    )
                    messages.success(request, f"成功修改教师信息：{teacher.Name}")
                return redirect("admin_dashboard")
            except Exception as e:
                messages.error(request, "修改失败，请检查输入内容。")
    else:
        form = EditTeacherForm(instance=teacher)

    return render(request, "edit_teacher.html", {"form": form, "teacher": teacher})


# 删除教师视图
def delete_teachers(request):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    if request.method == "POST":
        teacher_ids = request.POST.getlist("teacher_ids")
        try:
            with transaction.atomic():
                cnt = Teacher.objects.filter(TeacherID__in=teacher_ids).delete()[0]
                count = len(teacher_ids) if len(teacher_ids) <= cnt else cnt
                OperationLog.objects.create(
                    AdminID=get_object_or_404(Administrator, AdminID=admin_id),
                    Operation="删除教师",
                    Details=f"删除 {count} 名教师",
                    Timestamp=timezone.now(),
                )
                messages.success(request, f"成功删除 {count} 名教师")
            return redirect("admin_dashboard")
        except Exception as e:
            messages.error(request, "删除失败，请检查输入内容。")

    return redirect("admin_dashboard")


# 添加学生视图
def add_student(request):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    if request.method == "POST":
        form = AddStudentForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    student = form.save()
                    # 该学生是否已存在
                    OperationLog.objects.create(
                        AdminID=get_object_or_404(Administrator, AdminID=admin_id),
                        Operation="新增学生",
                        Details=f"新增学生：{student.Name}，邮箱：{student.Email}，密码：{student.Password}",
                        Timestamp=timezone.now(),
                    )
                    messages.success(request, f"成功添加学生：{student.Name}")
                return redirect("admin_dashboard")
            except Exception as e:
                messages.error(request, "添加学生失败，请检查输入内容。")
    else:
        form = AddStudentForm()

    return render(request, "add_student.html", {"form": form})


# 编辑学生信息视图
def edit_student(request, student_id):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    student = get_object_or_404(Student, StudentID=student_id)

    if request.method == "POST":
        form = EditStudentForm(request.POST, instance=student)
        if form.is_valid():
            try:
                with transaction.atomic():
                    old_name = student.Name
                    old_email = student.Email
                    old_pw = student.Password
                    form.save()
                    new_name = form.cleaned_data.get("Name")
                    new_email = form.cleaned_data.get("Email")
                    new_pw = form.cleaned_data.get("Password")
                    OperationLog.objects.create(
                        AdminID=get_object_or_404(Administrator, AdminID=admin_id),
                        Operation="编辑学生信息",
                        Details=f'编辑学生ID {student.StudentID}：从姓名 "{old_name}" 、邮箱 "{old_email}"、密码 "{old_pw}" 修改为姓名 "{new_name}" 、邮箱 "{new_email}、密码 "{new_pw}"',
                        Timestamp=timezone.now(),
                    )
                    messages.success(request, f"成功修改学生信息：{student.Name}")
                return redirect("admin_dashboard")
            except Exception as e:
                messages.error(request, "修改失败，请检查输入内容。")
    else:
        form = EditStudentForm(instance=student)

    return render(request, "edit_student.html", {"form": form, "student": student})


# 删除学生视图
def delete_students(request):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    if request.method == "POST":
        student_ids = request.POST.getlist("student_ids")
        try:
            with transaction.atomic():
                cnt = Student.objects.filter(StudentID__in=student_ids).delete()[
                    0
                ]  # 返回删除的数量
                count = len(student_ids) if len(student_ids) <= cnt else cnt
                OperationLog.objects.create(
                    AdminID=get_object_or_404(Administrator, AdminID=admin_id),
                    Operation="删除学生",
                    Details=f"删除 {count} 名学生",
                    Timestamp=timezone.now(),
                )
                messages.success(request, f"成功删除 {count} 名学生")
            return redirect("admin_dashboard")
        except Exception as e:
            messages.error(request, "删除失败，请检查输入内容。")

    return redirect("admin_dashboard")


# API KEY 管理视图
def api_key_management(request):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        messages.error(request, "无权限访问 API KEY 管理模块")
        return redirect("login")

    api_keys = APIKey.objects.all()

    context = {
        "api_keys": api_keys,
    }
    return render(request, "api_key_management.html", context)


# 添加 API KEY 视图
def add_api_key(request):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    if request.method == "POST":
        form = AddAPIKeyForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    api_key = form.save()
                    OperationLog.objects.create(
                        AdminID=get_object_or_404(Administrator, AdminID=admin_id),
                        Operation="新增 API Key 分配",
                        Details=f'为教师 "{api_key.TeacherID.Name}" 新增 API Key：模型 "{api_key.Model}"，版本 "{api_key.Version}"，KeyValue "{api_key.KeyValue}"，状态 {"启用" if api_key.Status else "禁用"}',
                        Timestamp=timezone.now(),
                    )
                    messages.success(
                        request,
                        f"成功新增API KEY分配：{api_key.TeacherID.Name} - {api_key.KeyValue}",
                    )
                return redirect("api_key_management")
            except Exception as e:
                messages.error(request, "添加API KEY失败，请检查输入内容。")
    else:
        form = AddAPIKeyForm()

    return render(request, "add_api_key.html", {"form": form})


# 编辑 API KEY 视图
def edit_api_key(request, key_id):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    api_key = get_object_or_404(APIKey, KeyID=key_id)

    if request.method == "POST":
        form = EditAPIKeyForm(request.POST, instance=api_key)
        if form.is_valid():
            try:
                with transaction.atomic():  # 确保API Key更新和操作日志记录为原子操作
                    old_teacher = api_key.TeacherID.Name
                    old_model = api_key.Model
                    old_version = api_key.Version
                    old_key_value = api_key.KeyValue
                    form.save()
                    new_teacher = form.cleaned_data.get("TeacherID").Name
                    new_model = form.cleaned_data.get("Model")
                    new_version = form.cleaned_data.get("Version")
                    new_key_value = form.cleaned_data.get("KeyValue")
                    OperationLog.objects.create(
                        AdminID=get_object_or_404(Administrator, AdminID=admin_id),
                        Operation="编辑 API Key 信息",
                        Details=f'将 API Key ID {api_key.KeyID} 从教师 "{old_teacher}" 修改为教师 "{new_teacher}"，模型 "{old_model}" -> "{new_model}"，版本 "{old_version}" -> "{new_version}"，KeyValue "{old_key_value}" -> "{new_key_value}"',
                        Timestamp=timezone.now(),
                    )
                    messages.success(
                        request,
                        f"成功修改API KEY信息：{api_key.TeacherID.Name} - {api_key.KeyValue}",
                    )
                return redirect("api_key_management")
            except Exception as e:
                messages.error(request, "修改失败，请检查输入内容。")

    else:
        form = EditAPIKeyForm(instance=api_key)

    return render(request, "edit_api_key.html", {"form": form, "api_key": api_key})


# 切换 API KEY 状态视图
def toggle_api_key_status(request, key_id):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    api_key = get_object_or_404(APIKey, KeyID=key_id)
    api_key.Status = not api_key.Status
    try:
        with transaction.atomic():
            api_key.save()
            status = "启用" if api_key.Status else "禁用"
            OperationLog.objects.create(
                AdminID=get_object_or_404(Administrator, AdminID=admin_id),
                Operation="切换 API Key 状态",
                Details=f'将 API Key ID {api_key.KeyID} 的状态切换为 {"启用" if api_key.Status else "禁用"}，教师 "{api_key.TeacherID.Name}"，KeyValue "{api_key.KeyValue}"',
                Timestamp=timezone.now(),
            )
            messages.success(
                request,
                f"成功{status}API KEY分配：{api_key.TeacherID.Name} - {api_key.KeyValue}",
            )
    except Exception as e:
        messages.error(request, "切换状态失败。")
    return redirect("api_key_management")


# 删除 API KEY 视图
def delete_api_keys(request):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    if request.method == "POST":
        key_ids = request.POST.getlist("key_ids")
        api_keys = APIKey.objects.filter(KeyID__in=key_ids)
        cnt = api_keys.count()
        try:
            with transaction.atomic():
                for api_key in api_keys:
                    OperationLog.objects.create(
                        AdminID=get_object_or_404(Administrator, AdminID=admin_id),
                        Operation="删除 API Key 分配",
                        Details=f'删除 API Key ID {api_key.KeyID}，教师 "{api_key.TeacherID.Name}"，模型 "{api_key.Model}"，版本 "{api_key.Version}"，KeyValue "{api_key.KeyValue}"',
                        Timestamp=timezone.now(),
                    )
                api_keys.delete()
                count = len(key_ids) if len(key_ids) <= cnt else cnt
                messages.success(request, f"成功删除 {count} 个API Key分配")
            return redirect("api_key_management")
        except Exception as e:
            messages.error(request, "删除失败，请检查输入内容。")

    return redirect("api_key_management")


# 查看操作日志视图
def view_operation_logs(request):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        messages.error(request, "无权限访问操作日志")
        return redirect("login")

    admin = get_object_or_404(Administrator, AdminID=admin_id)
    logs = OperationLog.objects.all().order_by("-Timestamp")

    # 添加分页，每页50条
    paginator = Paginator(logs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "logs": page_obj,
    }
    return render(request, "view_operation_logs.html", context)


# 编辑试题prompt视图
def edit_question_prompt(request, question_id):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    question = get_object_or_404(Question, QuestionID=question_id)

    if request.method == "POST":
        form = EditPromptForm(request.POST, instance=question)
        if form.is_valid():
            try:
                with transaction.atomic():
                    old_prompt = question.Prompt
                    form.save()
                    new_prompt = form.cleaned_data.get("Prompt")

                    # 记录操作日志
                    OperationLog.objects.create(
                        AdminID=get_object_or_404(Administrator, AdminID=admin_id),
                        Operation="编辑试题 Prompt",
                        Details=f'编辑试题 ID {question.QuestionID} "{question.Title}" 的 Prompt，从 "{old_prompt}" 修改为 "{new_prompt}"',
                        Timestamp=timezone.now(),
                    )

                    messages.success(request, f"成功编辑 prompt：{question.Title}")
                return redirect("admin_dashboard")
            except Exception as e:
                messages.error(request, "编辑失败，请检查输入内容。")
        else:
            messages.error(request, "编辑失败，请检查输入内容。")
    else:
        form = EditPromptForm(instance=question)

    context = {
        "form": form,
        "question": question,
    }
    return render(request, "edit_prompt.html", context)


# 添加试题视图
def add_question(request):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    if request.method == "POST":
        form = AddQuestionForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    question = form.save()
                    # 记录操作日志
                    OperationLog.objects.create(
                        AdminID=get_object_or_404(Administrator, AdminID=admin_id),
                        Operation="添加试题",
                        Details=f'添加试题 ID {question.QuestionID} "{question.Title}" 至课程 "{question.CourseID.Name}"',
                        Timestamp=timezone.now(),
                    )
                    messages.success(request, f"成功添加试题：{question.Title}")
                return redirect("admin_dashboard")
            except Exception as e:
                messages.error(request, "添加试题失败，请检查输入内容。")
        else:
            messages.error(request, "添加试题失败，请检查输入内容。")
    else:
        form = AddQuestionForm()

    return render(request, "add_question.html", {"form": form})


# =====================
# 教师相关视图
# =====================
# 以下视图需要教师权限访问


# 课程创建视图
def create_course(request):
    teacher_id = request.session.get("teacher_id")
    if not teacher_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    course = form.save(commit=False)
                    course.TeacherID = Teacher.objects.get(
                        TeacherID=request.session["teacher_id"]
                    )
                    course.save()
                    messages.success(request, f"成功添加课程：{course.Name}")
                return redirect("teacher_dashboard")
            except Exception as e:
                messages.error(request, "添加课程失败，请检查输入内容。")
    else:
        form = CourseForm()

    return render(request, "create_course.html", {"form": form})


# 课程删除视图
def delete_courses(request):
    teacher_id = request.session.get("teacher_id")
    if not teacher_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    if request.method == "POST":
        course_ids = request.POST.getlist("course_ids")
        try:
            with transaction.atomic():
                cnt = Course.objects.filter(
                    CourseID__in=course_ids,
                    TeacherID__TeacherID=request.session["teacher_id"],
                ).delete()[0]
                count = len(course_ids) if len(course_ids) <= cnt else cnt
                messages.success(request, f"成功删除 {count} 门课程")
            return redirect("teacher_dashboard")
        except Exception as e:
            messages.error(request, "删除失败，请检查输入内容。")

    return redirect("teacher_dashboard")


# 课程详情视图
def course_detail(request, course_id):
    teacher_id = request.session.get("teacher_id")
    if not teacher_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    teacher = get_object_or_404(Teacher, TeacherID=request.session["teacher_id"])
    courseid = get_object_or_404(Course, CourseID=course_id, TeacherID=teacher)
    students = StudentCourse.objects.filter(CourseID=courseid)
    # 获取该课程的所有试题
    questions = Question.objects.filter(CourseID=courseid).order_by("-CreatedAt")

    context = {
        "teacher": teacher,
        "course": courseid,
        "students": students,
        "questions": questions,
    }
    return render(request, "course_detail.html", context)


# 试题详情视图
def grade_answers(request, course_id, question_id):
    teacher_id = request.session.get("teacher_id")
    if not teacher_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    teacher = get_object_or_404(Teacher, TeacherID=teacher_id)
    course = get_object_or_404(Course, CourseID=course_id, TeacherID=teacher)
    question = get_object_or_404(Question, QuestionID=question_id, CourseID=course)

    # 获取教师拥有的有效 API Key，按模型和版本排序
    teacher_api_keys = APIKey.objects.filter(TeacherID=teacher, Status=True).order_by(
        "Model", "Version"
    )

    # 获取所有学生提交的答案
    answers = StudentAnswer.objects.filter(QuestionID=question).select_related(
        "StudentID"
    )  # select_related 用于优化查询性能，避免多次查询数据库, 但是只能用于 ForeignKey 或 OneToOneField
    # 通过 select_related("StudentID") 获取学生信息
    # answers是一个 QuerySet 对象，可以用于迭代

    answer_feedbacks = []
    for answer in answers:  # 遍历所有答案
        # 检查是否有评分
        has_feedback = ScoringFeedback.objects.filter(AnswerID=answer).exists()

        # 获取该答案最新的评分反馈
        latest_feedback = (
            ScoringFeedback.objects.filter(AnswerID=answer)
            .order_by("-CreatedAt")
            .first()
        )

        # 获取该答案最新的最终评分反馈
        final_feedback = (
            ScoringFeedback.objects.filter(AnswerID=answer, IsFinal=True)
            .order_by("-CreatedAt")
            .first()
        )

        # 将结果添加到列表中
        answer_feedbacks.append(
            {
                "answer": answer,
                "latest_feedback": latest_feedback,
                "cur_feedback": final_feedback or latest_feedback,
                "has_feedback": has_feedback,
            }
        )

    context = {
        "teacher": teacher,
        "course": course,
        "question": question,
        "answers": answers,
        "teacher_api_keys": teacher_api_keys,
        "answer_feedbacks": answer_feedbacks,
    }
    return render(request, "grade_answers.html", context)


# 智能批量打分视图
@require_POST
def batch_ai_grade(request, course_id, question_id):
    teacher_id = request.session.get("teacher_id")
    if not teacher_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    teacher = get_object_or_404(Teacher, TeacherID=teacher_id)
    course = get_object_or_404(Course, CourseID=course_id, TeacherID=teacher)
    question = get_object_or_404(Question, QuestionID=question_id, CourseID=course)

    selected_answer_ids = request.POST.getlist("answer_ids[]")
    model_choice = request.POST.get("model_choice")

    if not model_choice:
        return JsonResponse(
            {"status": "error", "message": "请选择一个大模型进行评分。"}
        )

    # 获取教师选择的 API Key
    try:
        api_key = APIKey.objects.get(KeyID=model_choice, TeacherID=teacher, Status=True)
    except APIKey.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "未找到指定的有效 API Key。"}
        )

    results = {}

    # 使用事务处理整个批量评分逻辑
    with transaction.atomic():
        for answer_id in selected_answer_ids:
            try:
                answer = StudentAnswer.objects.get(
                    AnswerID=answer_id, QuestionID=question
                )
            except StudentAnswer.DoesNotExist:
                results[answer_id] = {"status": "error", "message": "答案不存在。"}
                continue  # 跳过不存在的答案

            # 检查是否已经有未发布的自动评分
            # if answer.feedbacks.filter(IsFinal=False).exists():
            #     results[answer_id] = {"status": "warning", "message": "已在评价中。"}
            #     continue  # 跳过已在评分中的答案

            # 获取答案内容
            if answer.Content:
                answer_content = answer.Content
            else:
                answer_content = ""

            if not answer_content:
                # 答案内容为空或无法读取
                ScoringFeedback.objects.create(
                    AnswerID=answer,
                    Score=0,
                    Feedback="无法读取答案内容。",
                    CreatedAt=timezone.now(),
                    IsFinal=False,
                )
                results[answer_id] = {
                    "status": "error",
                    "message": "无法读取答案内容。",
                }
                continue

            # 调用相应的大模型进行评分
            try:
                if api_key.Model.lower().startswith("gpt"):
                    judge_result = get_judge_from_gpt(
                        answer_content,
                        question.Prompt,
                        api_key.KeyValue,
                        api_key.Version,
                    )
                elif api_key.Model.lower().startswith("qwen"):
                    judge_result = get_judge_from_qwen(
                        answer_content,
                        question.Prompt,
                        api_key.KeyValue,
                        api_key.Version,
                    )
                    print("judge_result", judge_result)
                else:
                    judge_result = {
                        "score": None,
                        "reason": "无效的大模型选择(仅支持GPT和Qwen)",
                    }

                if judge_result.get("score") is not None:
                    # 保存评分结果和反馈
                    ScoringFeedback.objects.create(
                        AnswerID=answer,
                        Score=judge_result["score"],
                        Feedback=judge_result["reason"],
                        CreatedAt=timezone.now(),
                        IsFinal=False,
                    )
                    results[answer_id] = {"status": "success", "message": "评分完成。"}
                else:
                    # API 调用失败
                    ScoringFeedback.objects.create(
                        AnswerID=answer,
                        Score=0,
                        Feedback=judge_result.get("reason", "AI评分失败。"),
                        CreatedAt=timezone.now(),
                        IsFinal=False,
                    )
                    results[answer_id] = {"status": "error", "message": "AI评分失败。"}
            except Exception as e:  # 记录异常
                ScoringFeedback.objects.create(
                    AnswerID=answer,
                    Score=0,
                    Feedback="AI评分过程中发生错误。",
                    CreatedAt=timezone.now(),
                    IsFinal=False,
                )
                results[answer_id] = {
                    "status": "error",
                    "message": "AI评分过程中发生错误。",
                }

    print("results", results)
    return JsonResponse({"status": "success", "results": results})


# 查看和评分答案
def view_and_grade_answer(request, course_id, question_id, answer_id):
    teacher_id = request.session.get("teacher_id")
    if not teacher_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    teacher = get_object_or_404(Teacher, TeacherID=teacher_id)
    course = get_object_or_404(Course, CourseID=course_id, TeacherID=teacher)
    question = get_object_or_404(Question, QuestionID=question_id, CourseID=course)
    answer = get_object_or_404(StudentAnswer, AnswerID=answer_id, QuestionID=question)

    # 获取所有该题的学生答案
    # 按照AnswerID排序，以便获取前后答案
    all_answers = StudentAnswer.objects.filter(QuestionID=question).order_by("AnswerID")
    answer_ids = list(all_answers.values_list("AnswerID", flat=True))
    current_index = answer_ids.index(answer_id)
    previous_id = answer_ids[current_index - 1] if current_index > 0 else None
    next_id = (
        answer_ids[current_index + 1] if current_index < len(answer_ids) - 1 else None
    )

    # 获取最新的评分记录
    scoring_feedback = answer.feedbacks.order_by("-CreatedAt").first()

    # scoring_feedback = (
    #     answer.feedbacks.filter(IsFinal=False).order_by("-CreatedAt").first()
    # )
    # if not scoring_feedback:
    #     scoring_feedback = (
    #         answer.feedbacks.filter(IsFinal=True).order_by("-CreatedAt").first()
    #     )

    if request.method == "POST":
        form = GradeAnswerForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():  # 确保评分更新和答案状态更新为原子操作
                    score = form.cleaned_data.get("Score")
                    feedback = form.cleaned_data.get("Feedback")

                    if scoring_feedback:  # 更新现有的评分记录
                        scoring_feedback.Score = (
                            score if score is not None else scoring_feedback.Score
                        )
                        scoring_feedback.Feedback = (
                            feedback if feedback else scoring_feedback.Feedback
                        )
                        scoring_feedback.IsFinal = True
                        scoring_feedback.CreatedAt = timezone.now()
                        scoring_feedback.save()
                    else:  # 创建新的评分记录
                        ScoringFeedback.objects.create(
                            AnswerID=answer,
                            Score=score,
                            Feedback=feedback,
                            CreatedAt=timezone.now(),
                            IsFinal=True,
                        )
                    # 更新答案确认时间
                    answer.ConfirmedAt = timezone.now()
                    answer.save()
                    messages.success(request, "成功确认并发布评价。")
                return redirect(
                    # "grade_answers", course_id=course_id, question_id=question_id
                    "view_and_grade_answer",
                    course_id=course_id,
                    question_id=question_id,
                    answer_id=answer_id,
                )
            except Exception as e:
                messages.error(request, "提交失败，请检查您的输入。")
        else:
            messages.error(request, "提交失败，请检查您的输入。")
    else:
        form = GradeAnswerForm()

    context = {
        "teacher": teacher,
        "course": course,
        "question": question,
        "answer": answer,
        "form": form,
        "previous_id": previous_id,
        "next_id": next_id,
        "scoring_feedback": scoring_feedback,
    }
    return render(request, "view_and_grade_answer.html", context)


# 导入评价视图
def import_ai_feedback(request, course_id, question_id, answer_id):
    teacher_id = request.session.get("teacher_id")
    if not teacher_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    # teacher = get_object_or_404(Teacher, TeacherID=teacher_id)
    answer = get_object_or_404(
        StudentAnswer, AnswerID=answer_id, QuestionID__CourseID=course_id
    )

    # 获取最新的非最终评分记录
    scoring_feedback = (
        answer.feedbacks.filter(IsFinal=False).order_by("-CreatedAt").first()
    )

    if not scoring_feedback:
        scoring_feedback = (
            answer.feedbacks.filter(IsFinal=True).order_by("-CreatedAt").first()
        )  # 获取最新的最终评分记录
        if not scoring_feedback:
            return JsonResponse({"status": "error", "message": "没有可导入的评价。"})

    data = {
        "score": scoring_feedback.Score,
        "feedback": scoring_feedback.Feedback,
    }

    return JsonResponse({"status": "success", "data": data})


# 修改课程信息视图
def edit_course(request, course_id):
    teacher_id = request.session.get("teacher_id")
    if not teacher_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    teacher = get_object_or_404(Teacher, TeacherID=teacher_id)
    course = get_object_or_404(Course, CourseID=course_id, TeacherID=teacher)

    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    messages.success(request, f"成功修改课程信息：{course.Name}")
                return redirect("course_detail", course_id=course.CourseID)
            except Exception as e:
                messages.error(request, "修改失败，请检查输入内容。")
    else:
        form = CourseForm(instance=course)

    return render(request, "edit_course.html", {"form": form, "course": course})


# 往课程里添加学生视图
def add_students(request, course_id):
    teacher_id = request.session.get("teacher_id")
    if not teacher_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    teacher = get_object_or_404(Teacher, TeacherID=teacher_id)
    course = get_object_or_404(Course, CourseID=course_id, TeacherID=teacher)

    if request.method == "POST":
        student_names = request.POST.getlist("name")
        student_emails = request.POST.getlist("email")
        added_count = 0
        try:
            with transaction.atomic():
                for name, email in zip(student_names, student_emails):
                    if name and email:
                        student, created = Student.objects.get_or_create(
                            Name=name, Email=email
                        )
                        if created:
                            student.Password = make_password(
                                "123456"
                            )  # 默认密码，可后续通知学生更改
                            student.save()
                        StudentCourse.objects.get_or_create(
                            StudentID=student, CourseID=course
                        )
                added_count = len(set(student_emails))
                messages.success(
                    request, f"成功往 {course.Name} 添加 {added_count} 名学生"
                )
        except Exception as e:
            messages.error(request, "添加学生失败，请检查输入内容。")
        return redirect("course_detail", course_id=course.CourseID)

    return render(request, "add_students.html", {"course": course})


# 从课程里删除学生视图
def remove_students(request, course_id):
    teacher_id = request.session.get("teacher_id")
    if not teacher_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    teacher = get_object_or_404(Teacher, TeacherID=teacher_id)
    course = get_object_or_404(Course, CourseID=course_id, TeacherID=teacher)

    if request.method == "POST":
        student_ids = request.POST.getlist("student_ids")
        try:
            with transaction.atomic():
                cnt = StudentCourse.objects.filter(
                    StudentID__StudentID__in=student_ids, CourseID=course
                ).delete()[0]
                count = len(student_ids) if len(student_ids) <= cnt else cnt
                messages.success(request, f"成功从 {course.Name} 删除 {count} 名学生")
            return redirect("course_detail", course_id=course.CourseID)
        except Exception as e:
            messages.error(request, "删除学生失败，请检查输入内容。")

    return redirect("course_detail", course_id=course.CourseID)


# 创建试题视图
def create_question(request, course_id):
    teacher_id = request.session.get("teacher_id")
    if not teacher_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    teacher = get_object_or_404(Teacher, TeacherID=teacher_id)
    course = get_object_or_404(Course, CourseID=course_id, TeacherID=teacher)

    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    question = form.save(commit=False)
                    question.CourseID = course
                    if question.IsOpen and not question.OpenAt:
                        question.OpenAt = timezone.now()
                    question.save()
                    messages.success(request, f"成功创建试题：{question.Title}")
                return redirect("course_detail", course_id=course.CourseID)
            except Exception as e:
                messages.error(request, "创建试题失败，请检查输入内容。")
    else:
        form = QuestionForm()

    return render(request, "create_question.html", {"form": form, "course": course})


# 删除试题视图
def delete_questions(request, course_id):
    teacher_id = request.session.get("teacher_id")
    if not teacher_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    teacher = get_object_or_404(Teacher, TeacherID=teacher_id)
    course = get_object_or_404(Course, CourseID=course_id, TeacherID=teacher)

    if request.method == "POST":
        question_ids = request.POST.getlist("question_ids")
        try:
            with transaction.atomic():
                cnt = Question.objects.filter(
                    QuestionID__in=question_ids, CourseID=course
                ).delete()[0]
                count = len(question_ids) if len(question_ids) <= cnt else cnt
                messages.success(request, f"成功删除 {count} 道试题")
            return redirect("course_detail", course_id=course.CourseID)
        except Exception as e:
            messages.error(request, "删除试题失败，请检查输入内容。")

    return redirect("course_detail", course_id=course.CourseID)


# 编辑试题信息视图
def edit_question(request, course_id, question_id):
    teacher_id = request.session.get("teacher_id")
    if not teacher_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    teacher = get_object_or_404(Teacher, TeacherID=teacher_id)
    course = get_object_or_404(Course, CourseID=course_id, TeacherID=teacher)
    question = get_object_or_404(Question, QuestionID=question_id, CourseID=course)

    if request.method == "POST":
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            try:
                with transaction.atomic():
                    question = form.save(commit=False)
                    if question.IsOpen and not question.OpenAt:
                        question.OpenAt = timezone.now()
                    question.save()
                    messages.success(request, f"成功修改试题信息：{question.Title}")
                return redirect("course_detail", course_id=course.CourseID)
            except Exception as e:
                messages.error(request, "修改失败，请检查输入内容。")
    else:
        form = QuestionForm(instance=question)

    return render(
        request,
        "edit_question.html",
        {"form": form, "course": course, "question": question},
    )


# 公开/封闭试题视图
def toggle_question_visibility(request, course_id, question_id):
    teacher_id = request.session.get("teacher_id")
    if not teacher_id:
        messages.error(request, "无权限访问")
        return redirect("login")

    teacher = get_object_or_404(Teacher, TeacherID=teacher_id)
    course = get_object_or_404(Course, CourseID=course_id, TeacherID=teacher)
    question = get_object_or_404(Question, QuestionID=question_id, CourseID=course)

    try:
        with transaction.atomic():
            question.IsOpen = not question.IsOpen
            if question.IsOpen and not question.OpenAt:
                question.OpenAt = timezone.now()
            elif not question.IsOpen:
                question.OpenAt = None
            question.save()

            status = "公开" if question.IsOpen else "封闭"
            messages.success(request, f"成功{status}试题：{question.Title}")
    except Exception as e:
        messages.error(request, "操作失败。")
    return redirect("course_detail", course_id=course.CourseID)


# =====================
# 学生相关视图
# =====================
# 以下视图需要学生权限访问


# 通过课程ID或名称搜索并加入课程
def join_course(request):
    student_id = request.session.get("student_id")
    if not student_id:
        messages.error(request, "无权限访问学生主页")
        return redirect("login")

    # student = Student.objects.get(StudentID=student_id)

    if request.method == "POST":
        course_search = request.POST.get("course_search")
        # 搜索课程ID或名称
        courses = Course.objects.filter(
            Q(CourseID__icontains=course_search) | Q(Name__icontains=course_search)
        )
        return render(
            request,
            "join_course.html",
            {"courses": courses, "course_search": course_search},
        )

    return render(request, "join_course.html")


# 确认加入课程
def confirm_join_course(request, course_id):
    student_id = request.session.get("student_id")
    if not student_id:
        messages.error(request, "无权限访问学生主页")
        return redirect("login")

    student = Student.objects.get(StudentID=student_id)
    course = Course.objects.get(CourseID=course_id)

    # 检查是否已加入
    if StudentCourse.objects.filter(StudentID=student, CourseID=course).exists():
        messages.info(request, f"您已加入课程：{course.CourseID} - {course.Name}")
    else:
        StudentCourse.objects.create(StudentID=student, CourseID=course)
        messages.success(request, f"成功加入课程：{course.CourseID} - {course.Name}")

    return redirect("student_dashboard")


# 退出课程视图
def leave_course(request):
    student_id = request.session.get("student_id")
    if not student_id:
        messages.error(request, "无权限访问学生主页")
        return redirect("login")

    student = Student.objects.get(StudentID=student_id)

    if request.method == "POST":
        course_ids = request.POST.getlist("course_ids")
        try:
            with transaction.atomic():
                courses = Course.objects.filter(
                    CourseID__in=course_ids, student_courses__StudentID=student
                )
                cnt = courses.count()
                StudentCourse.objects.filter(
                    StudentID=student, CourseID__in=courses
                ).delete()
                count = len(course_ids) if len(course_ids) <= cnt else cnt
                messages.success(request, f"成功退出 {count} 门课程")
            return redirect("student_dashboard")
        except Exception as e:
            messages.error(request, "退出失败，请检查输入内容。")
    # 获取学生已加入的课程
    enrolled_courses = StudentCourse.objects.filter(StudentID=student)
    return render(request, "leave_course.html", {"enrolled_courses": enrolled_courses})


# 查看公开试题视图
def student_course_detail(request, course_id):
    student_id = request.session.get("student_id")
    if not student_id:
        messages.error(request, "无权限访问学生主页")
        return redirect("login")

    student = Student.objects.get(StudentID=student_id)
    course = Course.objects.get(CourseID=course_id)
    # 授课老师
    teacher = Teacher.objects.get(TeacherID=course.TeacherID.TeacherID)

    # 检查学生是否已加入该课程
    if not StudentCourse.objects.filter(StudentID=student, CourseID=course).exists():
        messages.error(request, "您未加入该课程")
        return redirect("student_dashboard")

    # 获取公开的试题
    questions = Question.objects.filter(CourseID=course, IsOpen=True).order_by(
        "-CreatedAt"
    )

    # 获取学生的历史记录，并预加载最终评分反馈
    student_answers = StudentAnswer.objects.filter(
        StudentID=student, QuestionID__CourseID=course
    ).prefetch_related(
        Prefetch(
            "feedbacks",
            queryset=ScoringFeedback.objects.filter(IsFinal=True),
            to_attr="final_feedbacks",
        )
    )

    # 用于显示试题提交状态
    answered_question_ids = student_answers.values_list(
        "QuestionID__QuestionID", flat=True
    )  # .values_list() 返回一个元组列表，表示每个对象的指定字段的值

    context = {
        "course": course,
        "questions": questions,
        "student_answers": student_answers,
        "answered_question_ids": answered_question_ids,
        "teacher": teacher,
    }
    return render(request, "student_course_detail.html", context)


# 查看试题视图+提交答案
def view_question(request, course_id, question_id):
    student_id = request.session.get("student_id")
    if not student_id:
        messages.error(request, "无权限访问学生主页")
        return redirect("login")

    student = Student.objects.get(StudentID=student_id)
    course = Course.objects.get(CourseID=course_id)

    # 检查学生是否已加入该课程
    if not StudentCourse.objects.filter(StudentID=student, CourseID=course).exists():
        messages.error(request, "您未加入该课程")
        return redirect("student_dashboard")

    question = get_object_or_404(
        Question, QuestionID=question_id, CourseID=course, IsOpen=True
    )  # 检查试题是否公开
    student_answer = (
        StudentAnswer.objects.filter(
            QuestionID=question.QuestionID, StudentID=student.StudentID
        )
        .order_by("-SubmittedAt")  # 按提交时间降序排列
        .first()
    )  # 获取学生最新提交的答案

    # 检查此前是否已提交答案
    existing_answer = (
        StudentAnswer.objects.filter(StudentID=student, QuestionID=question)
        .order_by("-SubmittedAt")  # 按提交时间降序排列
        .first()
    )  # 获取学生最新提交的答案

    if request.method == "POST":  # 处理提交答案
        form = SubmitAnswerForm(request.POST, request.FILES)  # 从请求中获取表单数据
        if form.is_valid():  # 检查表单数据是否有效
            try:
                with transaction.atomic():  # 确保答案提交和评分删除的原子性
                    # 检查是否已提交答案, SubmitAnswerForm已经保证file和content有且仅有一个不为空
                    content = form.cleaned_data.get("Content")
                    file = form.cleaned_data.get("File")
                    if file:
                        import os

                        # 如果是文件，手动保存文件到uploaded_files目录，读取文件内容作为content
                        file_path = os.path.join("uploaded_files", file.name)
                        with open(file_path, "wb+") as destination:
                            for chunk in file.chunks():  # 分块写入文件
                                destination.write(chunk)
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()  # 读取文件内容
                    # 创建或获取学生答案，如果已有答案则更新内容和提交时间，否则创建新答案
                    student_answer, created = StudentAnswer.objects.get_or_create(
                        QuestionID=question,
                        StudentID=student,
                        defaults={
                            "Content": content,
                            "SubmittedAt": timezone.now(),
                        },
                    )  # created为True表示新建答案，False表示更新答案
                    if not created:  # 如果已有答案，更新已有答案
                        student_answer.Content = content
                        student_answer.SubmittedAt = timezone.now()
                        student_answer.ConfirmedAt = None  # 清除之前的确认时间
                        # 找到之前的评分记录，如果有，将其删除（因为答案更新后，原评价无效了）
                        ScoringFeedback.objects.filter(
                            AnswerID=student_answer
                        ).delete()  # 删除之前的所有评分记录
                        student_answer.save()
                        messages.success(request, "成功更新答案")
                    else:
                        messages.success(request, "成功提交答案")
                return redirect("student_course_detail", course_id=course_id)
            except Exception as e:
                messages.error(request, "提交失败，请检查您的答案。")
        else:
            messages.error(request, "提交失败，请检查您的答案。")
    else:
        form = SubmitAnswerForm(instance=existing_answer)

    context = {
        "question": question,
        "course": course,
        "form": form,
        "student_answer": student_answer,
        "existing_answer": existing_answer,
    }
    return render(
        request,
        "view_question.html",
        context,
    )


# 查看历史记录视图
def student_history_detail(request, course_id, answer_id):
    student_id = request.session.get("student_id")
    if not student_id:
        messages.error(request, "无权限访问学生主页")
        return redirect("login")

    student = get_object_or_404(Student, StudentID=student_id)
    answer = get_object_or_404(
        StudentAnswer,
        AnswerID=answer_id,
        StudentID=student,
        QuestionID__CourseID=course_id,
    )
    question = answer.QuestionID
    scoring_feedback = (
        ScoringFeedback.objects.filter(AnswerID=answer, IsFinal=True)
        .order_by("-CreatedAt")
        .first()
    )  # 获取最终评分，越新的评分越靠前

    context = {
        "course_id": course_id,
        "answer": answer,
        "question": question,
        "scoring_feedback": scoring_feedback,
    }
    return render(request, "student_history_detail.html", context)
