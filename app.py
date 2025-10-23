#Flask server
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from flask_migrate import Migrate
from flask import send_from_directory
from flask import flash

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
    file_type = db.Column(db.String(20))

    uploader = db.relationship('User', backref=db.backref('files', lazy=True))

    @staticmethod
    def get_file_type(filename): 
        if filename.lower().endswith(('.png','.jpg','.jpeg','.gif')): 
            return 'image' 
        elif filename.lower().endswith(('.pdf')): 
            return 'pdf' 
        elif filename.lower().endswith(('.txt')): 
            return 'text' 
        return 'other'

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

        flash('Registration successful ! You can try to login now','success')
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
            flash('Login successful !','success')
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
        flash('Please login first.', 'warning')
        return redirect (url_for('login'))
   
    user = User.query.get(session['user_id'])

    if not user or not user.is_admin:
            flash('Admin privileges required.', 'danger')
            return redirect(url_for('index'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part in the request.', 'warning')
            return redirect(url_for('upload'))
        

        file=request.files['file']
        if file.filename == '':
            flash('No selected file.', 'warning')
            return redirect(url_for('upload'))
        
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
                is_public=True if user.is_admin else request.form.get("make_public") == 'on',
                uploader=user,
                file_type=File.get_file_type(filename)
                
            )
            db.session.add(new_file)
            db.session.commit()

            flash(f'File {filename} uploaded successfuly!', 'success')
            return redirect(url_for('list_files'))
        
    return render_template('upload.html')

@app.route('/files', methods=['GET'])
def list_files():
    if 'user_id' not in session:
        flash('Please login to view files')
        return redirect (url_for('login'))
    
    user= User.query.get(session['user_id'])
    search_query = request.args.get('search','').strip()
    file_type = request.args.get('file_type','').strip()

    if user.is_admin:
        files = File.query
    else:
        files = File.query.filter((File.is_public == True) | (File.user_id == user.id))
    # Apply search filter
    if search_query:
        files = files.filter(File.filename.ilike(f'%{search_query}%'))
    if file_type:
        files = files.filter(File.file_type == file_type)

    files = files.order_by(File.id.desc()).options(db.joinedload(File.uploader)).all()

    for file in files:
        try:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.size = os.path.getsize(filepath)
        except:
            file.size=0 

    return render_template('files.html', files=files, search_query=search_query, file_type=file_type)

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

        flash('File deleted successfully','success')
    except Exception as e:
        flash('Error deleting file','error')

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
    
@app.route('/preview/<int:file_id>')
def preview_file(file_id):
    if 'user_id'not in session:
        flash('Please login first')
        return redirect(url_for('login'))
    
    file = File.query.get_or_404(file_id)

    if not file.is_public and file.user_id != session['user_id']:
        flash('You do not have permission to view this file')
        return redirect(url_for('list_files'))
    
    try:
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            file.filename,
            as_attachment=False
        )
    except FileNotFoundError:
        flash('File not found on server')
        return redirect(url_for('list_files'))
    
@app.route('/view/<int:file_id>')
def view_file(file_id):
    file = File.query.get_or_404(file_id)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file_type = File.get_file_type(file.filename)

    file_content = None
    if file_type == 'text':
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()

    return render_template('view.html', file=file, file_type=file_type, file_content=file_content)

if __name__ == '__main__':
    app.run(debug=True)
