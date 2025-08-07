#Flask server
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from flask_migrate import Migrate
from flask import send_from_directory

app = Flask(__name__)
app.config['UPLOAD_FOLDER']='uploads'
app.config['MAX_CONTENT_LENGTH']= 8 * 1024 * 1024
app.config['SECRET_KEY'] = 'js69'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///user.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False

db= SQLAlchemy(app)
migrate= Migrate(app, db)

class File(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    size = db.Column(db.Integer)
    upload_date=db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_public = db.Column (db.Boolean, default=False)

    uploader = db.relationship('User', backref=db.backref('files', lazy=True))

class User(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


with app.app_context():
    db.create_all()

    if not User.query.filter_by(username='admin').first():
        admin = User(
            username = 'admin',
            password=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()

#ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)



#route
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/app')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Both fields are required to field in')
            return redirect (url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken !')
            return redirect (url_for('register'))
        
        new_user = User(
            username=username,
            password=generate_password_hash(password),
            is_admin=False
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful ! You can try to login now')
        return redirect (url_for('login'))
    
    return render_template('register.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            flash('Login successful !')
            return redirect(url_for('index'))
        
        flash('Invalid username or password')
        return redirect(url_for('login'))

    return render_template('login.html')
    
    

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('landing'))


#handling file upload route
@app.route('/upload', methods=['GET','POST'], endpoint='upload')
def upload_file():

    if 'user_id' not in session:
        flash('Please login first')
        return redirect (url_for('login'))
   
    user = User.query.get(session['user_id'])

    if not user or not user.is_admin:
        flash('Admin privileges required')
        return redirect(url_for('index'))

    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))
    

    file=request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        file_size= os.path.getsize(filepath)

#save files in db
        new_file = File(
            filename=filename,
            size=file_size,
            user_id=user.id,
            is_public=request.form.get("make_public") == 'on',
            uploader=user
            
        )
        db.session.add(new_file)
        db.session.commit()

        flash(f'File {filename} uploaded successfuly!')
        return redirect(url_for('index'))

@app.route('/files')
def list_files():
    if 'user_id' not in session:
        flash('Please login to view files')
        return redirect (url_for('login'))
    
    user= User.query.get(session['user_id'])

    files = File.query.options(db.joinedload(File.uploader)).filter(
        (File.is_public == True) |
        (File.user_id == user.id)
    ).all()

   
    for file in files:
        try:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.size = os.path.getsize(filepath)
        except:
            file.size=0 #not found

    return render_template('files.html', files=files)

@app.route('/delete/<int:file_id>', methods=['POST'])
def delete_file(file_id):
    if'user_id' not in session:
        flash('Please login first')
        return redirect (url_for('login'))
    
    file = File.query.get_or_404(file_id)

    #permission
    if file.user_id != session['user_id'] and not session.get('is_admin'):
        flash('You do not have permission to delete this file')
        return redirect(url_for('list_files'))
    
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        if os.path.exists(filepath):
            os.remove(filepath)

        db.session.delete(file)
        db.session.commit()

        flash('File deleted successfully')
    except Exception as e:
        flash('Error deleting file')

    return redirect(url_for('list_files'))

@app.route('/download/<int:file_id>')
def download_file(file_id):
    if 'user_id' not in session:
        flash('Please login first')
        return redirect(url_for('login'))
    
    file = File.query.get_or_404(file_id)
    
    if not file.is_public and file.user_id != session['user_id']:
        flash('You do not have permission to download this file')
        return redirect(url_for('list_files'))
    
    try:
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            file.filename,
            as_attachment=True
        )
    except FileNotFoundError:
        flash('File not found on server')
        return redirect(url_for('list_files'))
    
if __name__ == '__main__':
    app.run(debug=True)
