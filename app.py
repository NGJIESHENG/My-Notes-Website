#Flask server
from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER']='uploads'
app.config['MAX_CONTENT_LENGTH']= 8 * 1024 * 1024

#ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

#homepage route
@app.route('/')
def index():
    return render_template('index.html')

#handling file upload route
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'

    file=request.files['file']

    if file.filename == '':
        return 'No selected file'
    
    if file:
        file.save(os.path.join(app.config['UPLOAD_FOLDER'],file.filename))
        return f'File{file.filename} uploaded successfully!'

if __name__ == '__main__':
    app.run(debug=True)
