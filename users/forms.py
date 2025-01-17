# users/forms.py

from django import forms
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
from django.forms import ModelForm
from django.contrib.auth.hashers import make_password


class AddTeacherForm(ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="密码")

    class Meta:
        model = Teacher
        fields = ["Name", "Email", "Password"]
        widgets = {
            "Name": forms.TextInput(attrs={"class": "form-control"}),
            "Email": forms.EmailInput(attrs={"class": "form-control"}),
            "Password": forms.PasswordInput(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        teacher = super().save(commit=False)
        teacher.Password = make_password(self.cleaned_data["password"])
        if commit:
            teacher.save()
        return teacher


class AddStudentForm(ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="密码")

    class Meta:
        model = Student
        fields = ["Name", "Email", "Password"]
        widgets = {
            "Name": forms.TextInput(attrs={"class": "form-control"}),
            "Email": forms.EmailInput(attrs={"class": "form-control"}),
            "Password": forms.PasswordInput(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        student = super().save(commit=False)
        student.Password = make_password(self.cleaned_data["password"])
        if commit:
            student.save()
        return student


class EditTeacherForm(ModelForm):
    # password = forms.CharField(
    #     widget=forms.PasswordInput, label="密码", required=False
    # )

    class Meta:
        model = Teacher
        fields = ["Name", "Email", "Password"]
        widgets = {
            "Name": forms.TextInput(attrs={"class": "form-control"}),
            "Email": forms.EmailInput(attrs={"class": "form-control"}),
            "Password": forms.PasswordInput(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        teacher = super().save(commit=False)
        password = self.cleaned_data.get("Password")
        if password:
            teacher.Password = make_password(password)
        if commit:
            teacher.save()
        return teacher


class EditStudentForm(ModelForm):
    # password = forms.CharField(widget=forms.PasswordInput, label="密码", required=False)

    class Meta:
        model = Student
        fields = ["Name", "Email", "Password"]
        widgets = {
            "Name": forms.TextInput(attrs={"class": "form-control"}),
            "Email": forms.EmailInput(attrs={"class": "form-control"}),
            "Password": forms.PasswordInput(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        student = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            student.Password = make_password(password)
        if commit:
            student.save()
        return student


class AddAPIKeyForm(ModelForm):
    class Meta:
        model = APIKey
        fields = ["TeacherID", "Model", "Version", "KeyValue", "Status"]
        widgets = {
            "TeacherID": forms.Select(attrs={"class": "form-control"}),
            "Model": forms.TextInput(attrs={"class": "form-control"}),
            "Version": forms.TextInput(attrs={"class": "form-control"}),
            "KeyValue": forms.TextInput(attrs={"class": "form-control"}),
            "Status": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class EditAPIKeyForm(ModelForm):
    class Meta:
        model = APIKey
        fields = ["TeacherID", "Model", "Version", "KeyValue"]
        widgets = {
            "TeacherID": forms.Select(attrs={"class": "form-control"}),
            "Model": forms.TextInput(attrs={"class": "form-control"}),
            "Version": forms.TextInput(attrs={"class": "form-control"}),
            "KeyValue": forms.TextInput(attrs={"class": "form-control"}),
        }


class AddQuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["CourseID", "Title", "Content", "ScoringCriteria", "Prompt", "IsOpen"]
        widgets = {
            "CourseID": forms.Select(attrs={"class": "form-control"}),
            "Title": forms.TextInput(attrs={"class": "form-control"}),
            "Content": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "ScoringCriteria": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "Prompt": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "IsOpen": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_Title(self):
        title = self.cleaned_data.get("Title")
        if not title:
            raise forms.ValidationError("标题不可为空。")
        return title


class EditPromptForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["Prompt"]
        widgets = {
            "Prompt": forms.Textarea(attrs={"class": "form-control", "rows": 20}),
        }

    def clean_Prompt(self):
        prompt = self.cleaned_data.get("Prompt")
        # if not prompt:
        #     raise forms.ValidationError("Prompt 不可为空。")
        return prompt


class CourseForm(ModelForm):
    class Meta:
        model = Course
        fields = ["Name", "Description"]
        widgets = {
            "Name": forms.TextInput(attrs={"class": "form-control"}),
            "Description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class QuestionForm(ModelForm):
    class Meta:
        model = Question
        fields = [
            "Title",
            "Content",
            "ScoringCriteria",
            "Prompt",
            "IsOpen",
        ]
        #    "OpenAt"]
        widgets = {
            "Title": forms.TextInput(attrs={"class": "form-control"}),
            "Content": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "ScoringCriteria": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "Prompt": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "IsOpen": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            # "OpenAt": forms.DateTimeInput(
            #     attrs={"class": "form-control", "type": "datetime-local"}
            # ),
        }


# 提交答案表单
class SubmitAnswerForm(forms.ModelForm):
    File = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control-file"}),
    )  # File得到的是一个文件对象
    # 没有文件路径，文件路径是在服务器上的，不会传到客户端

    Content = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 10}),
    )  # Content得到的是一个字符串。rows表示文本框的行数，显示10行，如果内容超过10行，会自动滚动显示

    class Meta:  # 通过Meta类指定表单的元数据
        model = StudentAnswer  # 表单对应的模型：StudentAnswer
        fields = ["Content"]  # 表单包含的字段：Content

    def clean(self):
        cleaned_data = super().clean()  # 调用父类的clean方法，获取验证后的数据
        content = cleaned_data.get("Content")
        file = cleaned_data.get("File")

        # 验证逻辑：Content 和 File 至少提供一个，且不能同时提供
        if not content and not file:
            raise forms.ValidationError("请提交答案内容或上传文件。")
        if content and file:
            raise forms.ValidationError("请提交答案内容或上传文件，不能同时提交。")

        if file:  # 如果上传了文件，检查文件格式
            import os

            ext = os.path.splitext(file.name)[1].lower()
            if ext not in [".txt", ".md"]:
                raise forms.ValidationError("仅支持txt、markdown文档格式。")

        return cleaned_data


class GradeAnswerForm(forms.ModelForm):
    class Meta:
        model = ScoringFeedback
        fields = ["Score", "Feedback"]
        widgets = {
            "Score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "max": "200",
                    "step": "0.1",
                    "id": "id_Score",
                }
            ),
            "Feedback": forms.Textarea(
                attrs={"class": "form-control", "rows": 5, "id": "id_Feedback"}
            ),
        }

    def clean_Score(self):
        score = self.cleaned_data.get("Score")
        if score is not None and (score < 0 or score > 200):
            raise forms.ValidationError("分数必须在0到200之间。")
        return score
