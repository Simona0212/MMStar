# users/signals.py

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Administrator
from django.contrib.auth.hashers import make_password


@receiver(post_migrate)
def create_default_admin(sender, **kwargs):
    if sender.name == "users":
        if not Administrator.objects.filter(Name="ADMIN").exists():
            Administrator.objects.create(
                Name="ADMIN",
                Email="admin@example.com",
                Password=make_password("123456"),  # 使用加密存储密码
                # make_password()函数使用默认的PBKDF2算法，迭代数为150000，生成一个128字节的哈希值
            )
            print("默认管理员已创建")
