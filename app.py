# Flask backend (app.py)
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import jwt
import datetime


app = Flask(__name__)
CORS(app)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/task_manager'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://sql12755669:IQaf21EhcB@sql12.freesqldatabase.com:3306/sql12755669'

app.config['SECRET_KEY'] = 'tsm1'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date=db.Column(db.DateTime, default=datetime.datetime.now)
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    reminder_time = db.Column(db.Integer, nullable=False)  # in minutes before due_date
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    complete = db.Column(db.Boolean, default=False)


with app.app_context():
    db.create_all()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not all(k in data for k in ('username', 'password', 'email')):
        return jsonify({'message': 'Missing required fields'}), 400

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], password=hashed_password, email=data['email'])

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully!'}), 201
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'message': 'Error: User could not be registered.'}), 400


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Invalid input'}), 400

    try:
        user = User.query.filter_by(username=data['username']).first()
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({'message': 'Internal server error'}), 500

    if user and bcrypt.check_password_hash(user.password, data['password']):
        try:
            payload = {
                'id': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }
            print(f"Payload: {payload}")  
            print(f"SECRET_KEY: {app.config['SECRET_KEY']}") 

           
            token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

           
            if isinstance(token, bytes):
                token = token.decode('utf-8')

            return jsonify({'token': token}), 200
        except Exception as e:
            print(f"JWT encoding error: {e}") 
            return jsonify({'message': 'Token generation failed'}), 500
    else:
        return jsonify({'message': 'Invalid credentials'}), 401








@app.route('/get/<int:user_id>', methods=['GET'])
def get_tasks_for_user(user_id):
 
    tasks = Task.query.filter_by(user_id=user_id).all()

    task_list = [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date,
            "reminder_time": task.reminder_time,
            "user_id": task.user_id,
            "complete":task.complete
        }
        for task in tasks
    ]

   
    if not task_list:
        return jsonify({"message": "No tasks found for this user"}), 404

    return jsonify(task_list), 200



@app.route('/tasks', methods=['POST'])
def create_task():
    user_id = request.json['user_id']
    title = request.json['title']
    description = request.json['description']
    due_date = request.json['due_date']
    reminder_time = int(request.json['reminder_time'])  

    new_task = Task(user_id=user_id, title=title, description=description, due_date=due_date, reminder_time=reminder_time)
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'message': 'Task created successfully!', 'task': {
        'id': new_task.id,
        'user_id': new_task.user_id,
        'title': new_task.title,
        'description': new_task.description,
        'due_date': new_task.due_date,
        'reminder_time': new_task.reminder_time
    }}), 201


@app.route('/update/<int:id>/', methods=['PUT', 'OPTIONS'])
def update_task(id):
   
    if request.method == 'OPTIONS':
        return jsonify({'message': 'Preflight request successful'}), 200
    

    task = Task.query.get(id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.get_json()
    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)
    task.due_date = data.get('due_date', task.due_date)
    task.reminder_time = int(data.get('reminder_time', task.reminder_time))

    db.session.commit()

    return jsonify({
        'message': 'Task updated successfully',
        'task': {
            'title': task.title,
            'description': task.description,
            'due_date': task.due_date,
            'reminder_time': task.reminder_time
        }
    }), 200

# ######################################################






@app.route('/delete/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404
    
    try:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted successfully!'}), 200
    except Exception as e:
        return jsonify({'message': 'Error: Task could not be deleted.', 'error': str(e)}), 400


@app.route('/complete/<int:task_id>', methods=['PUT'])
def complete_task(task_id):
    task=Task.query.get(task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404
    data = request.get_json()
    task.complete = data.get('complete', task.complete)
    
    db.session.commit()

    return jsonify({
        'message': 'Task updated successfully',
        'task': {
            'complete': task.complete           
        }
    }), 200



if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True)

