# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 其他路径...
    path("admin_dashboard/", views.admin_dashboard, name="admin_dashboard"),
    # admin相关URL
    path("admin_dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("add_teacher/", views.add_teacher, name="add_teacher"),
    path("edit_teacher/<int:teacher_id>/", views.edit_teacher, name="edit_teacher"),
    path("delete_teachers/", views.delete_teachers, name="delete_teachers"),
    path("add_student/", views.add_student, name="add_student"),
    path("edit_student/<int:student_id>/", views.edit_student, name="edit_student"),
    path("delete_students/", views.delete_students, name="delete_students"),
    # API Key 管理相关URL
    path("api_key_management/", views.api_key_management, name="api_key_management"),
    path("add_api_key/", views.add_api_key, name="add_api_key"),
    path("edit_api_key/<int:key_id>/", views.edit_api_key, name="edit_api_key"),
    path(
        "toggle_api_key_status/<int:key_id>/",
        views.toggle_api_key_status,
        name="toggle_api_key_status",
    ),
    path("delete_api_keys/", views.delete_api_keys, name="delete_api_keys"),
    path("view_operation_logs/", views.view_operation_logs, name="view_operation_logs"),
    path(
        "edit_question_prompt/<int:question_id>/",
        views.edit_question_prompt,
        name="edit_question_prompt",
    ),
    path("add_question/", views.add_question, name="add_question"),
    # teacher相关URL
    path("teacher_dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
    path("create_course/", views.create_course, name="create_course"),
    path("delete_courses/", views.delete_courses, name="delete_courses"),
    path("course/<int:course_id>/", views.course_detail, name="course_detail"),
    path("course/<int:course_id>/edit/", views.edit_course, name="edit_course"),
    path(
        "course/<int:course_id>/add_students/", views.add_students, name="add_students"
    ),
    path(
        "course/<int:course_id>/remove_students/",
        views.remove_students,
        name="remove_students",
    ),
    path(
        "course/<int:course_id>/create_question/",
        views.create_question,
        name="create_question",
    ),
    path(
        "course/<int:course_id>/delete_questions/",
        views.delete_questions,
        name="delete_questions",
    ),
    path(
        "course/<int:course_id>/edit_question/<int:question_id>/",
        views.edit_question,
        name="edit_question",
    ),
    path(
        "course/<int:course_id>/toggle_visibility/<int:question_id>/",
        views.toggle_question_visibility,
        name="toggle_question_visibility",
    ),
    path(
        "teacher_course/<int:course_id>/question/<int:question_id>/grade/",
        views.grade_answers,
        name="grade_answers",
    ),
    path(
        "teacher_course/<int:course_id>/question/<int:question_id>/answer/<int:answer_id>/view_grade/",
        views.view_and_grade_answer,
        name="view_and_grade_answer",
    ),
    path(
        "teacher_course/<int:course_id>/question/<int:question_id>/answer/<int:answer_id>/import_ai_feedback/",
        views.import_ai_feedback,
        name="import_ai_feedback",
    ),
    path(
        "teacher_course/<int:course_id>/question/<int:question_id>/batch_ai_grade/",
        views.batch_ai_grade,
        name="batch_ai_grade",
    ),
    # student相关URL
    path("student_dashboard/", views.student_dashboard, name="student_dashboard"),
    path("join_course/", views.join_course, name="join_course"),
    path(
        "confirm_join_course/<int:course_id>/",
        views.confirm_join_course,
        name="confirm_join_course",
    ),
    path("leave_course/", views.leave_course, name="leave_course"),
    path(
        "student_course/<int:course_id>/",
        views.student_course_detail,
        name="student_course_detail",
    ),
    path(
        "student_course/<int:course_id>/question/<int:question_id>/",
        views.view_question,
        name="view_question",
    ),
    path(
        "student_course/<int:course_id>/history/<int:answer_id>/",
        views.student_history_detail,
        name="student_history_detail",
    ),
]
