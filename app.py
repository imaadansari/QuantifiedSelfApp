from flask import Flask, render_template, request, redirect, send_file, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
import matplotlib.pyplot as plt
import pandas as pd
import jwt
from functools import wraps
from flask_caching import Cache
import os
from werkzeug.utils import secure_filename
from flask_celery import make_celery


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///records.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'thisismysecretkey'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config.update(CELERY_CONFIG={
    'broker_url': 'redis://localhost:6379',
    'result_backend': 'db+sqlite:///records.db',
})


cache = Cache(config={'CACHE_TYPE': 'RedisCache'})
cache.init_app(app)

db = SQLAlchemy(app)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token')

        if not token:
            return jsonify({'message': 'token is missing'})

        try:
            data = jwt.decode(
                token, f"{app.config['SECRET_KEY']}", algorithms=["HS256"])
        except:
            return render_template('token_expired.html')

        return f(*args, **kwargs)
    return decorated


class User(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)

    def __repr__(self) -> str:
        return f"{self.sno}-{self.user_id}-{self.password}"


class Tracker_Instance(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(200))
    tracker = db.Column(db.String(200))
    timestamp = db.Column(
        db.String(200), default=datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
    value = db.Column(db.Float)
    note = db.Column(db.String(500))

    def serialize(self):
        return {
            'sno': self.sno,
            'user_id': self.user_id,
            'tracker': self.tracker,
            'timestamp': self.timestamp,
            'value': self.value,
            'note': self.note
        }

    def __repr__(self) -> str:
        return f"{self.sno}-{self.tracker}-{self.value}"


class Tracker(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    user_sno = db.Column(db.Integer)
    user_id = db.Column(db.String(200))
    tracker = db.Column(db.String(200), nullable=False)

    def __repr__(self) -> str:
        return f"{self.sno}-{self.user_id}-{self.tracker}"


celery = make_celery(app)


@app.route("/", methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        allUsers = User.query.all()
        l = []
        e = []
        for i in allUsers:
            l.append(i.user_id)
            e.append(i.email)

        if (username not in l) and (email not in e):
            user = User()
            user.user_id = username
            user.password = password
            user.email = email
            db.session.add(user)
            db.session.commit()
            return redirect("/login")
        else:
            return render_template("username_email_taken.html")
    return render_template("signup.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(user_id=username).first()

        allUsers = User.query.all()

        l = []
        for i in allUsers:
            l.append(i.user_id)

        if (username not in l) or (user.password != password):
            return render_template("invalid_username_pass.html")

        elif user.password == password:
            token = jwt.encode({"user": f"{user.user_id}", "exp": datetime.now(
                tz=timezone.utc) + timedelta(minutes=30)}, key=f'{app.config["SECRET_KEY"]}')
            return redirect(f"dashboard/{user.sno}?token={token}")
    return render_template("login.html")


@app.route("/dashboard/<int:sno>", methods=['GET', 'POST'])
@token_required
def dashboard(sno):
    user = User.query.filter_by(sno=sno).first()
    trackers = Tracker.query.filter_by(user_sno=user.sno)
    token = request.args.get('token')
    l = []
    trackers_json = []
    for i in trackers:
        if i.tracker not in l:
            l.append(i.tracker)
            trackers_json.append({'tracker': i.tracker})

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(trackers_json)
    return render_template("dashboard.html", user=user, trackers=l, trackers_length=len(l), token=token)


@app.route("/dashboard/<int:sno>/create", methods=['GET', 'POST'])
@token_required
def addTracker(sno):
    user = User.query.filter_by(sno=sno).first()
    tracker = request.get_json()
    tracker_card = Tracker(
        user_sno=user.sno, user_id=user.user_id, tracker=tracker.get('title'))
    token = request.args.get('token')

    existing_trackers = Tracker.query.filter_by(user_sno=user.sno)
    existing_tracker_list = []
    for i in existing_trackers:
        existing_tracker_list.append(i.tracker)
    t = tracker.get('title')

    if t not in existing_tracker_list:
        db.session.add(tracker_card)
        db.session.commit()
        print("adding")
        return jsonify(tracker_card.tracker)
    return redirect(f"/dashboard/{user.sno}/create?token={token}")


@app.route("/dashboard/<int:sno>/delete", methods=['GET', 'POST'])
@token_required
def delete_tracker(sno):
    user = User.query.filter_by(sno=sno).first()

    tracker_card = request.get_json()
    print(tracker_card.get('tracker'))
    tracker = tracker_card.get('tracker')

    trackers = Tracker_Instance.query.filter_by(
        user_id=user.user_id, tracker=tracker)
    tracker_card = Tracker.query.filter_by(
        user_id=user.user_id, tracker=tracker)

    for i in tracker_card:
        db.session.delete(i)

    for i in trackers:
        db.session.delete(i)
    db.session.commit()
    return jsonify({'result': 'Ok'}), 200


@app.route("/view-tracker/<int:sno>/<tracker>", methods=['GET', 'POST'])
@token_required
def view_tracker(sno, tracker):
    user = User.query.filter_by(sno=sno).first()
    token = request.args.get('token')

    trackers = Tracker_Instance.query.filter_by(
        user_id=user.user_id, tracker=tracker)

    t = []
    for i in trackers:
        t.append(i)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify([i.serialize() for i in trackers])

    return render_template("view_tracker.html", user=user, tracker=tracker, token=token)


@app.route("/view-tracker/<int:sno>/<tracker>/create", methods=['POST'])
@token_required
def create_tracker_instance(sno, tracker):
    print(sno, tracker)
    user = User.query.filter_by(sno=sno).first()

    user_input = request.get_json()

    value = float(user_input.get('value'))
    note = user_input.get('note')
    tracker_instance = Tracker_Instance(
        user_id=user.user_id, tracker=tracker, value=value, note=note)
    db.session.add(tracker_instance)
    db.session.commit()

    return jsonify(tracker_instance.serialize())


@app.route("/update-tracker-instance/<int:tracker_sno>", methods=['GET', 'POST'])
@token_required
def update_tracker(tracker_sno):
    tracker_instance = Tracker_Instance.query.filter_by(
        sno=tracker_sno).first()
    user = User.query.filter_by(user_id=tracker_instance.user_id).first()
    token = request.args.get('token')

    if request.method == "POST":
        tracker_instance.value = float(request.form['value'])
        tracker_instance.note = request.form['note']
        tracker_instance.timestamp = request.form['timestamp']

        db.session.add(tracker_instance)
        db.session.commit()
        return redirect(f"/view-tracker/{user.sno}/{tracker_instance.tracker}?token={token}")

    return render_template("update_tracker_instance.html", tracker_instance=tracker_instance, user=user, token=token)


@app.route("/view-tracker/<int:user_sno>/<tracker>/delete", methods=['POST'])
@token_required
def delete_tracker_instance(user_sno, tracker):
    print(user_sno, tracker)
    tracker_sno = request.get_json().get('sno')
    db.session.delete(Tracker_Instance.query.filter_by(
        sno=tracker_sno).first())
    db.session.commit()
    return jsonify({'result': 'Ok'}), 200


@app.route("/view-report/<int:user_sno>/<tracker>", methods=['GET', 'POST'])
@token_required
@cache.cached(timeout=60)
def view_report(user_sno, tracker):

    user = User.query.filter_by(sno=user_sno).first()
    token = request.args.get('token')

    minval = db.session.query(func.min(Tracker_Instance.value)).filter(
        Tracker_Instance.tracker == tracker, Tracker_Instance.user_id == user.user_id).first()[0]
    maxval = db.session.query(func.max(Tracker_Instance.value)).filter(
        Tracker_Instance.tracker == tracker, Tracker_Instance.user_id == user.user_id).first()[0]
    avgval = db.session.query(func.avg(Tracker_Instance.value)).filter(
        Tracker_Instance.tracker == tracker, Tracker_Instance.user_id == user.user_id).first()[0]

    min_instance = Tracker_Instance.query.filter_by(
        tracker=tracker, value=minval, user_id=user.user_id).first()
    max_instance = Tracker_Instance.query.filter_by(
        tracker=tracker, value=maxval, user_id=user.user_id).first()

    trackers = Tracker_Instance.query.filter_by(
        user_id=user.user_id, tracker=tracker)

    values = []
    y=[]
    v=0
    for i in trackers:
        values.append(i.value)
        v+=1
        y.append(v)
    plt.plot(y,values)

    filename = f'{datetime.utcnow().strftime("plot%d%m%Y%H%M%S")}.png'

    plt.savefig(f"static/userfiles/{filename}")
    plt.close()
    return render_template("report.html", min_instance=min_instance, avgval=avgval, max_instance=max_instance, user=user, plot_filename="userfiles/"+filename, token=token)


@app.route("/download-csv/<int:user_sno>/<tracker>", methods=['GET', 'POST'])
@token_required
def download_csv(user_sno, tracker):

    user = User.query.filter_by(sno=user_sno).first()
    trackers = Tracker_Instance.query.filter_by(
        user_id=user.user_id, tracker=tracker)

    df = pd.read_sql(trackers.statement, db.session.bind)
    df.drop(["sno", "user_id", "tracker"], axis=1, inplace=True)

    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    filename = f"static/userfiles/{user.user_id}_{tracker}_{timestamp}.csv"
    df.to_csv(filename)

    return send_file(filename, as_attachment=True)


@app.route('/import-values/<int:user_sno>/<tracker>', methods=['POST', 'GET'])
def import_values(user_sno, tracker):
    token = request.args.get('token')
    if request.method == 'POST':
        file = request.files['file']

        if file.filename == '':
            return redirect(f'/view-tracker/{user_sno}/{tracker}?token={token}')

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        df = pd.read_csv(f'static/uploads/{file.filename}')
        l = []
        for i in df.index:
            l.append({'timestamp': df['timestamp'][i],
                     'value': df['value'][i], 'note': df['note'][i]})
        print(l)
        add_values.delay(l, user_sno, tracker)
        return redirect(f'/dashboard/{user_sno}?token={token}')


@celery.task(name='app.add_values')
def add_values(l, user_sno, tracker):
    user = User.query.filter_by(sno=user_sno).first()
    for i in range(len(l)):
        tracker_instance = Tracker_Instance(
            user_id=user.user_id,
            tracker=tracker,
            timestamp=l[i]['timestamp'],
            value=float(l[i]['value']),
            note=l[i]['note']
        )
        db.session.add(tracker_instance)
    db.session.commit()
    return "values added"


if __name__ == '__main__':
    app.run(debug=True)
