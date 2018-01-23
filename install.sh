virtualenv --no-site-packaes env
source env/bin/active
pip install -r requirements.txt
nohup python manage.py runserver 0.0.0.0:8000
