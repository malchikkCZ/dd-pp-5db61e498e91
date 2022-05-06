from random import randint
import os

from flask_login import UserMixin
from werkzeug.utils import secure_filename

from app.main import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    todos = db.relationship('Todo', backref='user')


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(250))
    is_done = db.Column(db.Boolean(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        todo_dict = {
            '_id': self.id,
            'title': self.title,
            'description': self.description,
            'filename': self.filename,
            'is_done': self.is_done
        }

        return todo_dict

    @staticmethod
    def upload_file(request):
        try:
            req_file = request.files['file']
        except Exception as err:
            return ''

        filename = secure_filename(req_file.filename)
        basedir = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(basedir, 'static', 'uploads')
        if not os.path.exists(path):
            os.makedirs(path)

        full_path = os.path.join(path, filename)
        while os.path.isfile(full_path):
            extension = f'.{filename.split(".")[-1]}'
            filename = filename.replace(extension, '') + str(randint(1000, 9999)) + extension
            full_path = os.path.join(path, filename)
        
        req_file.save(full_path)

        return filename


db.create_all()