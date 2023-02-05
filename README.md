**Quantified Self App**

DESCRIPTION
----------------------
A Web-App that allows you to track various aspects of your life.


HOW TO RUN?
----------------------
The app runs on Linux based system or WSL if using Windows OS.

STEPS:
1 - Create a virtual environment and install all the necessary libraries.
USE COMMAND - pip install flask Flask-SQLAlchemy SQLAlchemy matplotlib pandas pyjwt Flask-Caching celery fpdf2 smtplib schedule

2 - Make sure you have redis installed on your machine.

3 - Open a terminal and start redis server
USE COMMAND - redis-server

4 - Open another terminal and start a celery worker.
USE COMMAND - celery -A app.celery worker --loglevel=info

5 - Open another terminal and start the flask server.
USE COMMAND - python app.py

6 - Open another terminal and to run send_mail.py to send regular emails.
USE COMMAND - python send_mail.py
  - Enter password and your app is running on localhost.


THANK YOU FOR USING QUANTIFIED SELF APP
----------------------

***END***



