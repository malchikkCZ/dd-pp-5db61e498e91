import functools

from flask import jsonify, request
from flask_login import current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from app.main import app, db
from app.models import User, Todo


def is_authenticated(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        if current_user.is_authenticated:
            user = current_user
            return f(user, *args, **kwargs)
        else:
            return jsonify({ 'Error': 'User not logged in' }), 401

    return inner


# # Todo routes, authenticated user only

# Index, show all active todos
@app.route('/', methods=['GET'])
@is_authenticated
def index(user):
    todos = Todo.query.filter_by(user_id = user.id)
    if todos:
        todos_array = [todo.to_dict() for todo in todos if todo.is_done == False]
        if len(todos_array) > 0:
            return jsonify(todos_array), 200
        else:
            return jsonify({ 'Success': 'No active todos for user' }), 200
    else:
        return jsonify({ 'Error': 'No todos for user' }), 404


# Show all done todos
@app.route('/todos/done', methods=['GET'])
@is_authenticated
def done_todos(user):
    todos = Todo.query.filter_by(user_id = user.id)
    if todos:
        todos_array = [todo.to_dict() for todo in todos if todo.is_done == True]
        if len(todos_array) > 0:
            return jsonify(todos_array), 200
        else:
            return jsonify({ 'Success': 'No done todos for user' }), 200
    else:
        return jsonify({ 'Error': 'No todos for user' }), 404


# Handle a single todo by its id
@app.route('/todos/<int:todo_id>', methods=['GET', 'POST'])
@is_authenticated
def single_todo(user, todo_id):
    todo = Todo.query.get(todo_id)
    if todo and todo.user_id != user.id:
        return jsonify({ 'Error': 'User not authenticated to view this todo' }), 401
    elif todo:
        # Change the state of todo if POST method 
        if request.method == 'POST':
            new_state = not todo.is_done
            todo.is_done = new_state
            db.session.commit()

            return jsonify({ 'Success': f'Todo marked as done: {new_state}' }), 200
        # Get the details of todo if GET method
        else:
            return jsonify([todo.to_dict()]), 200
    else:
        return jsonify({ 'Error': 'No such todo in database' }), 404


# Create a new todo
@app.route('/todos', methods=['POST'])
@is_authenticated
def create_todo(user):
    req = request.form

    new_todo = Todo(
        title = req['title'],
        description = req['description'],
        filename = Todo.upload_file(request),
        is_done = False,
        user_id = user.id
    )

    db.session.add(new_todo)
    db.session.commit()

    return jsonify({ 'Success': 'New todo added to the database' }), 200


# # User routes

# Register a new user
@app.route('/register', methods=['POST'])
def register():
    req = request.form
    if User.query.filter_by(username=req['username']).first():
        return jsonify({ 'Error': 'This username already exists' }), 400
    else:
        new_user = User(
            username = req['username'],
            password = generate_password_hash(req['password'], method='pbkdf2:sha256', salt_length=8)
        )
        db.session.add(new_user)
        db.session.commit()

        return jsonify({ 'Success': 'New user added to the database' }), 200


# Login an existing user
@app.route('/login', methods=['POST'])
def login():
    req = request.form
    user = User.query.filter_by(username=req['username']).first()
    if user and check_password_hash(user.password, req['password']):
        login_user(user)
        return jsonify({ 'Success': f'Logged in as {user.username}' }), 200
    else:
        return jsonify({ 'Error': 'Invalid username or password' }), 401


# Logout current user
@app.route('/logout', methods=['POST'])
@is_authenticated
def logout(user):
    logout_user()
    return jsonify({ 'Success': f'Logged out' }), 200
