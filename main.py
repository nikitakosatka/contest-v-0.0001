import sys
import traceback

from flask import Flask, render_template, redirect, request, session
from flask_sqlalchemy import SQLAlchemy

sys.excepthook = traceback.print_exception

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'kosatka'
db = SQLAlchemy(app)


class YandexLyceumStudent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(80), unique=False, nullable=False)
    surname = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    group = db.Column(db.String(80), unique=False, nullable=False)
    password = db.Column(db.String(255), unique=False, nullable=False)

    def __repr__(self):
        return '<YandexLyceumStudent {} {} {} {}>'.format(
            self.id, self.username, self.name, self.surname)


class SolutionAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(80), unique=False, nullable=False)
    code = db.Column(db.String(1000), unique=False, nullable=False)
    status = db.Column(db.String(50), unique=False, nullable=False)
    student_id = db.Column(db.Integer,
                           db.ForeignKey('yandex_lyceum_student.id'),
                           nullable=False)
    student = db.relationship('YandexLyceumStudent',
                              backref=db.backref('SolutionAttempts',
                                                 lazy=True))

    def __repr__(self):
        return '<SolutionAttempt {} {} {}>'.format(
            self.id, self.task, self.status)


db.create_all()

if not YandexLyceumStudent.query.filter_by(username='admin').first():
    admin = YandexLyceumStudent(username='admin',
                                email='admin@yandexlyceum.ru',
                                name='Админ',
                                surname='Админ',
                                group='admin',
                                password='admin')
    db.session.add(admin)
    db.session.commit()


@app.route('/', methods=['POST', 'GET'])
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template("login.html")

    elif request.method == 'POST':
        user = YandexLyceumStudent.query.filter_by(username=request.form['login']).first()
        if user:
            if user.password == request.form['password']:
                session['user_id'] = user.id
                session['username'] = user.username
                if session.get('username') == 'admin':
                    return redirect('/index')
                else:
                    return redirect('/index')
            return render_template("login.html", wrong_password=True)
        return render_template("login.html", wrong_password=True)


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'GET':
        return render_template("register.html")

    elif request.method == 'POST':
        db.session.add(YandexLyceumStudent(username=request.form['login'],
                                           email=request.form['email'],
                                           name=request.form['name'],
                                           surname=request.form['surname'],
                                           group=request.form['group'],
                                           password=request.form['password']))
        db.session.commit()
        return redirect("/login")


@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        if session.get('username') != 'admin':
            return render_template("index.html")
        else:
            solutions = SolutionAttempt.query.filter_by(status='На проверке').all()
            return render_template("index.html", admin=True, solutions=solutions)

    elif request.method == 'POST':
        if session.get('username') != 'admin':
            return render_template("index.html")
        else:
            if request.form.get("edit-solution") == "1":
                if request.form.get('ok') is not None:
                    sol = SolutionAttempt.query.filter_by(
                        id=int(request.form['solution-id'])).first()
                    new_sol = SolutionAttempt(task=sol.task,
                                              code=sol.code,
                                              id=sol.id,
                                              status='Зачтено',
                                              student_id=sol.student_id
                                              )
                    SolutionAttempt.query.filter_by(id=int(request.form['solution-id'])).delete()
                    db.session.add(new_sol)

                    db.session.commit()
                if request.form.get('no') is not None:
                    sol = SolutionAttempt.query.filter_by(
                        id=int(request.form['solution-id'])).first()
                    new_sol = SolutionAttempt(task=sol.task,
                                              code=sol.code,
                                              id=sol.id,
                                              status='На доработке',
                                              student_id=sol.student_id
                                              )
                    SolutionAttempt.query.filter_by(id=int(request.form['solution-id'])).delete()
                    db.session.add(new_sol)

                    db.session.commit()
            else:
                db.session.add(SolutionAttempt(task=request.form['task'],
                                               code=request.form['code'],
                                               status='На проверке',
                                               student_id=session['user_id']))
                db.session.commit()

            solutions = SolutionAttempt.query.filter_by(status='На проверке').all()
            return render_template("index.html", admin=True, solutions=solutions)


@app.route('/status')
def status():
    solutions = SolutionAttempt.query.filter_by().all()
    return render_template("status.html", solutions=solutions)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
