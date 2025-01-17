# users/models.py

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from django.conf import settings  # 用于引用自定义的 User 模型


# 自定义用户管理器
class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, role="student"):
        if not email:
            raise ValueError("Users must have an email address")
        if not name:
            raise ValueError("Users must have a name")

        email = self.normalize_email(email)
        user = self.model(email=email, name=name, role=role)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password):
        user = self.create_user(email, name, password, role="admin")
        user.is_admin = True
        user.save(using=self._db)
        return user


# 用户模型
class User(AbstractBaseUser):
    ROLE_CHOICES = (
        ("admin", "管理员"),
        ("teacher", "教师"),
        ("student", "学生"),
    )

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    email = models.EmailField(max_length=100, unique=True, null=True)  # , blank=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="student")

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return self.email if self.email else self.name

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin


class Administrator(models.Model):
    # user = models.OneToOneField(
    #     settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    # )
    AdminID = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=50, default="admin")
    Email = models.EmailField(max_length=100, null=True, unique=True)  # , blank=True)
    Password = models.CharField(max_length=255, default="123456")  # 加密存储

    class Meta:
        db_table = "Administrator"
        indexes = [
            models.Index(fields=["Email"], name="idx_admin_email"),
        ]

    def __str__(self):
        return self.Name


class OperationLog(models.Model):
    LogID = models.AutoField(primary_key=True)
    AdminID = models.ForeignKey(
        Administrator, on_delete=models.CASCADE, related_name="operation_logs"
    )
    Operation = models.CharField(max_length=200)
    Details = models.TextField()
    Timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "OperationLog"
        indexes = [
            models.Index(fields=["Timestamp"], name="idx_log_timestamp"),
        ]

    def __str__(self):
        return f"{self.Operation} by {self.AdminID.Name} at {self.Timestamp}"


class Teacher(models.Model):
    # user = models.OneToOneField(
    #     settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    # )
    TeacherID = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=50)
    Email = models.EmailField(max_length=100, null=True, unique=True)  # , blank=True)
    Password = models.CharField(max_length=255, default="123456")

    class Meta:
        db_table = "Teacher"
        indexes = [
            models.Index(fields=["Email"], name="idx_teacher_email"),
        ]

    def __str__(self):
        return self.Name


class APIKey(models.Model):
    KeyID = models.AutoField(primary_key=True)
    TeacherID = models.ForeignKey(
        Teacher, on_delete=models.CASCADE, related_name="api_keys"
    )
    Model = models.CharField(max_length=50)
    Version = models.CharField(max_length=20)
    KeyValue = models.CharField(max_length=255)
    Status = models.BooleanField(default=True)

    class Meta:
        db_table = "APIKey"
        indexes = [
            models.Index(
                fields=["TeacherID", "Status"], name="idx_apikey_teacher_status"
            ),
            models.Index(fields=["Model", "Version"], name="idx_apikey_model_version"),
        ]

    def __str__(self):
        return f"APIKey {self.KeyID} for {self.TeacherID.Name}"


class Course(models.Model):
    CourseID = models.AutoField(primary_key=True)
    TeacherID = models.ForeignKey(
        Teacher, on_delete=models.CASCADE, related_name="courses"
    )
    Name = models.CharField(max_length=100)
    Description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "Course"
        indexes = [
            models.Index(fields=["TeacherID"], name="idx_course_teacher"),
        ]

    def __str__(self):
        # return self.Name
        return f"{self.CourseID} - {self.Name}"


class Student(models.Model):
    # user = models.OneToOneField(
    #     settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    # )
    StudentID = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=50)
    Email = models.EmailField(max_length=100, null=True, unique=True)  # , blank=True)
    Password = models.CharField(max_length=255, default="123456")

    class Meta:
        db_table = "Student"
        indexes = [
            models.Index(fields=["Email"], name="idx_student_email"),
        ]

    def __str__(self):
        return self.Name


class StudentCourse(models.Model):
    StudentID = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="student_courses"
    )  # 外键关联学生表
    CourseID = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="student_courses"
    )  # 外键关联课程表

    class Meta:
        db_table = "StudentCourse"  # 表名
        unique_together = ("StudentID", "CourseID")  # 联合唯一索引
        indexes = [
            models.Index(
                fields=["StudentID", "CourseID"], name="idx_student_course"
            ),  # 经常需要根据StudentID和CourseID两个字段一起查询数据，故建立复合索引
        ]

    def __str__(self):
        return f"{self.StudentID.Name} enrolled in {self.CourseID.Name}"


class Question(models.Model):
    QuestionID = models.AutoField(primary_key=True)
    CourseID = models.ForeignKey(
        "Course", on_delete=models.CASCADE, related_name="questions"
    )
    Title = models.CharField(max_length=100)
    Content = models.TextField()
    ScoringCriteria = models.TextField(null=True, blank=True)
    Prompt = models.TextField(null=True, blank=True)
    CreatedAt = models.DateTimeField(
        default=timezone.now
    )  # timezone.now返回当前时间（带时区，默认为UTC，可通过settings.py修改）
    IsOpen = models.BooleanField(default=False)
    OpenAt = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "Question"
        indexes = [
            models.Index(
                fields=["CourseID", "IsOpen"], name="idx_question_course_open"
            ),  # 经常需要根据CourseID和IsOpen两个字段一起查询数据
            models.Index(fields=["CreatedAt"], name="idx_question_created_at"),
            # 经常需要根据CreatedAt字段排序
        ]

    def __str__(self):
        return self.Title


class StudentAnswer(models.Model):
    AnswerID = models.AutoField(
        primary_key=True
    )  # 主键，聚簇索引，按主键字段排序数据，用于快速定位行
    QuestionID = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="answers"
    )  # 非聚簇索引，加速按外键字段过滤或关联查询，避免全表扫描
    StudentID = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="answers"
    )  # 非聚簇索引，加速按外键字段过滤或关联查询，避免全表扫描
    Content = models.TextField(blank=True, null=True)
    SubmittedAt = models.DateTimeField(default=timezone.now)
    ConfirmedAt = models.DateTimeField(
        null=True, blank=True
    )  # 该答案的评分与反馈确认时间

    class Meta:
        db_table = "StudentAnswer"
        indexes = [
            models.Index(
                fields=["QuestionID", "StudentID"], name="idx_answer_question_student"
            ),  # 经常需要根据QuestionID和StudentID两个字段一起查询数据
            models.Index(fields=["SubmittedAt"], name="idx_answer_submitted_at"),
            # 经常需要根据SubmittedAt字段排序
        ]

    def __str__(self):
        return f"Answer {self.AnswerID} by {self.StudentID.Name}"


class ScoringFeedback(models.Model):
    FeedbackID = models.AutoField(primary_key=True)
    AnswerID = models.ForeignKey(
        StudentAnswer, on_delete=models.CASCADE, related_name="feedbacks"
    )
    Score = models.FloatField()
    Feedback = models.TextField(null=True, blank=True)
    CreatedAt = models.DateTimeField(default=timezone.now)
    IsFinal = models.BooleanField(default=False)

    class Meta:
        db_table = "ScoringFeedback"
        indexes = [
            models.Index(
                fields=["AnswerID", "IsFinal"], name="idx_feedback_answer_final"
            ),
            models.Index(fields=["CreatedAt"], name="idx_feedback_created_at"),
        ]

    def __str__(self):
        return f"Feedback {self.FeedbackID} for Answer {self.AnswerID.AnswerID}"
