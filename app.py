import os
import json
from flask import Flask, render_template, request, session, url_for, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = 'uploads'

socketio = SocketIO(app)
MESSAGE_HISTORY = 'message_history.json'

@app.route('/')
def sessions():
    return render_template('session.html')

@socketio.on('connect', namespace='/chat')
def handle_connect():
    with open(MESSAGE_HISTORY, 'r') as f:
        messages = json.load(f)
        for message in messages:
            if message['type'] == 'text':
                emit('receive_message', {'username': message['username'], 'message': message['message']})
            elif message['type'] == 'image':
                emit('receive_image', {'username': message['username'], 'img_url': message['img_url']})

@socketio.on('username', namespace='/chat')
def receive_username(username):
    session['username'] = username

@socketio.on('send_message', namespace='/chat')
def handle_message(message):
    with open(MESSAGE_HISTORY, 'r') as f:
        messages = json.load(f)

    messages.append({'type': 'text', 'username': session.get('username'), 'message': message})
    
    with open(MESSAGE_HISTORY, 'w') as f:
        json.dump(messages, f)
    
    emit('receive_message', {'username': session.get('username'), 'message': message}, broadcast=True)

@socketio.on('send_image', namespace='/chat')
def handle_image(data):
    filename = secure_filename(data['filename'])
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    with open(filepath, 'wb') as f:
        base64_data = data['file'].split(',', 1)[1]
        f.write(base64.b64decode(base64_data))
        
    img_url = url_for('uploaded_file', filename=filename)
    
    with open(MESSAGE_HISTORY, 'r') as f:
        messages = json.load(f)
        
    messages.append({'type': 'image', 'username': session.get('username'), 'img_url': img_url})
    
    with open(MESSAGE_HISTORY, 'w') as f:
        json.dump(messages, f)
        
    # Print the emitted data
    print({'username': session.get('username'), 'img_url': img_url})
    
    emit('receive_image', {'username': session.get('username'), 'img_url': img_url}, broadcast=True)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    if not os.path.exists(MESSAGE_HISTORY):
        with open(MESSAGE_HISTORY, 'w') as f:
            json.dump([], f)

    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
