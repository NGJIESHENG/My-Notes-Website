#Flask server
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER']='uploads'
app.config['MAX_CONTENT_LENGTH']= 8 * 1024 * 1024
app.config['SECRET_KEY'] = 'js69'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///user.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False

db= SQLAlchemy(app)

class User(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    username = db.column(db.String(80), unique=True, mullable=False)
    password = db.column(db.String(120), nullable=False)
    is_admin = db.column(db.Boolean, default=False)

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

#homepage route
@app.route('/')
def index():
    return render_template('index.html')

@app.routr('/register', methods=['GET', 'POST'])
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

    return render_template('login.html')
    
    

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))


#handling file upload route
@app.route('/upload', methods=['POST'])
def upload_file():

    if 'user_id' not in session:
        flash('Please login first')
        return redirect (url_for('login'))
   
    user=user.query.get(session['user_id'])

    if not user or not user.is_admin:
        flash('ADmin privileges required')
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
        file.save(os.path.join(app.config['UPLOAD_FOLDER'],file.filename))
        flash(f'File{file.filename} uploaded successfully!')
        return redirect(url_for('index'))
    

if __name__ == '__main__':
    app.run(debug=True)
