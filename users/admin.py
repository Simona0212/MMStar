# users/admin.py

from django.contrib import admin
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

admin.site.register(User)
admin.site.register(Administrator)
admin.site.register(OperationLog)
admin.site.register(Teacher)
admin.site.register(APIKey)
admin.site.register(Course)
admin.site.register(Student)
admin.site.register(StudentCourse)
admin.site.register(Question)
admin.site.register(StudentAnswer)
admin.site.register(ScoringFeedback)
