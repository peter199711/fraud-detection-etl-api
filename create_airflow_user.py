from airflow.models.user import User
from airflow.www.security import AirflowSecurityManager
from airflow import settings

# 建立一個 security manager 實例
security_manager = AirflowSecurityManager(settings.Session)

# 檢查使用者是否已存在
existing_user = security_manager.find_user(username="admin")

if not existing_user:
    # 如果使用者不存在，則建立新使用者
    # create_user 方法會自動處理密碼的雜湊加密
    user = security_manager.create_user(
        username="admin",
        email="admin@example.com",
        role_name="Admin", # 在 Airflow 2.0+ 中, 角色名稱是 "Admin"
        password="admin",
        first_name="Peter",
        last_name="User"
    )
    print("User 'admin' created successfully.")
else:
    print("User 'admin' already exists.")

