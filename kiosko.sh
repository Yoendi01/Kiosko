#! /bin/bash

source /home/yoendi/Programming/kiosko/.venv/bin/activate

python3 /home/yoendi/Programming/kiosko/manage.py runserver &

firefox localhost:8000

