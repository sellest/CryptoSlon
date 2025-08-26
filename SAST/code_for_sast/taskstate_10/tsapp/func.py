from flask import Flask
import jwt
from .sconfig import rteam, JWT_KEY

def create_app():
    from .sconfig import SECRET_KEY
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    app.secret_key = SECRET_KEY
    return app


def f_rid_get(request):
    rid = 0
    if request.cookies.get('rid'):
        rid = int(request.cookies.get('rid'))
        if rid >= len(rteam):
            rid = 0
    return rid


def f_task_acl(task, rid, uid):
    res = False
    if rid == 2:
        res = True
    if rid == 1:
        if task.private == False or (task.uid1 == uid and task.private == True):
            res = True
    if rid == 0:
        if task.uid1 == uid:
            res = True
    return res


def jwt_encod(user):
    jwt_data = {"id": user.id,"login": user.login}
    # VULNERABILITY FOUND: CWE-640 Lack of Expiration for Security Token
    # token = jwt.encode(jwt_data, JWT_KEY, algorithm="HS256")
```python
import os
import time
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Генерация токена для восстановления пароля
def generate_password_recovery_token(email):
    return s.dumps(email, salt='password-recovery')

# Проверка и извлечение токена для восстановления пароля
def verify_password_recovery_token(token, expiration=3600):  # Токен действителен 1 час
    try:
        email = s.loads(token, salt='password-recovery', max_age=expiration)
    except Exception as e:
        return None
    return email
```
    return token


def jwt_decod(token):
    jwt_data = jwt.decode(token, JWT_KEY, algorithms="HS256")
    return jwt_data