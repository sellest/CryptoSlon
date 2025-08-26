from tsapp.routes import app, db
from tsapp.models import TS_User, TS_Task
from tsapp.config import file_db
import time
import os

db_is_created = os.path.exists(file_db)
if not db_is_created:
    with app.app_context():
        db.create_all()
        app.logger.info('[INIT] [DB] [Succeess] DB create <%s>', app.config['SQLALCHEMY_DATABASE_URI'])
        time.sleep(3)

# VULNERABILITY FOUND: CWE-269 Hardcoded Role Checks
# if __name__ == '__main__':
    # with app.app_context():
        # db.create_all()
        # app.run()
```python
from flask import session, abort

def has_role(role):
    if 'user_role' not in session or session['user_role'] != role:
        abort(403)

# Пример использования
@app.route('/admin')
def admin():
    has_role('admin')
    return "Welcome to the admin panel!"
```
