from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, join_room, send
import os
from backend.models import User, Product, ServiceProvider 
from backend import app, db  # Import app and db from the package


socketio = SocketIO(app)

# Ensure the upload directories exist
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'images'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'videos'), exist_ok=True)

# User and Product models in models.py


# Home route
@app.route('/')
def index():
    services = ServiceProvider.query.all()
    products = Product.query.all()
    return render_template('index.html', services=services, products=products)

# Registration for Service Providers and Renters
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_type = request.form['user_type']
        username = request.form['username']
        password = request.form['password']
        
        if user_type == 'renter':
            user = User(username=username, password=password, role='renter')
        else:
            user = User(username=username, password=password, role='service_provider')
        
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            session['user_id'] = user.id
            session['role'] = user.role
            
            if user.role == 'renter':
                return redirect(url_for('renter_dashboard'))
            else:
                return redirect(url_for('service_provider_dashboard'))
        else:
            return 'Invalid credentials!'
    return render_template('login.html')

# Chat functionality using SocketIO
@socketio.on('join')
def on_join(data):
    room = data['user_id']
    join_room(room)
    send(f"User {data['user_id']} has joined the chat", to=room)

@socketio.on('send_message')
def handle_message(data):
    room = data['user_id']
    send({'message': data['message'], 'sender': 'self'}, to=room)

# Service provider dashboard
@app.route('/service_provider_dashboard')
def service_provider_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    services = ServiceProvider.query.filter_by(user_id=user_id).all()
    return render_template('dashboard.html', services=services)

# Renter dashboard
@app.route('/renter_dashboard')
def renter_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    products = Product.query.filter_by(user_id=user_id).all()
    return render_template('dashboard.html', products=products)

# Product upload for renters
@app.route('/upload_product', methods=['POST'])
def upload_product():
    product_name = request.form['product_name']
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(url_for('login'))

    images = request.files.getlist('product_images')
    videos = request.files.getlist('product_videos')
    
    image_paths = ",".join([secure_filename(img.filename) for img in images])
    video_paths = ",".join([secure_filename(vid.filename) for vid in videos])

    for img in images:
        img.save(os.path.join(app.config['UPLOAD_FOLDER'], 'images', secure_filename(img.filename)))
    
    for vid in videos:
        vid.save(os.path.join(app.config['UPLOAD_FOLDER'], 'videos', secure_filename(vid.filename)))

    product = Product(
        name=product_name,
        image_paths=image_paths,
        video_paths=video_paths,
        user_id=user_id
    )

    db.session.add(product)
    db.session.commit()
    
    return 'Product uploaded successfully!'

# Listing products
@app.route('/products')
def product_list():
    products = Product.query.all()
    return render_template('product_list.html', products=products)

# Listing services
@app.route('/services')
def service_list():
    services = ServiceProvider.query.all()
    return render_template('service_list.html', services=services)

# Chat route
@app.route('/chat')
def chat():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    return render_template('chat.html', user_id=user_id)

if __name__ == "__main__":
    socketio.run(app, debug=True)
