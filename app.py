from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import os
import random
import string

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///web3forms.db'
db = SQLAlchemy(app)

# Email setup (SMTP details)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'kisalshehara7@gmail.com'  # Your Gmail address
app.config['MAIL_PASSWORD'] = 'cdnj tdjd koas faba'  # App-specific password or your actual password (if using less secure apps)
app.config['MAIL_DEFAULT_SENDER'] = 'kisalshehara7@gmail.com'  # Default sender email

mail = Mail(app)

# Model for user registration
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    access_key = db.Column(db.String(32), unique=True, nullable=False)

# Generate random access key
def generate_access_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

# Home route for user registration and access key sending
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            flash('Email is already registered! We have sent the access key again.', 'info')
            access_key = user.access_key
        else:
            access_key = generate_access_key()
            new_user = User(email=email, access_key=access_key)
            db.session.add(new_user)
            db.session.commit()

            flash('Access key created! Check your email for the key.', 'success')

        # Send access key via email
        msg = Message('Your Access Key', recipients=[email])
        msg.body = f'Your access key is: {access_key}\n\nCopy the HTML form code below and replace "YOUR_ACCESS_KEY_HERE" with your key.'
        mail.send(msg)

    return render_template('index.html')

# Route to generate HTML form for the user
@app.route('/generate_form/<access_key>')
def generate_form(access_key):
    user = User.query.filter_by(access_key=access_key).first()
    if not user:
        flash('Invalid Access Key', 'danger')
        return redirect(url_for('index'))

    # Form code template to be copied by the user
    form_html = f'''
    <form action="http://127.0.0.1:5000/submit" method="POST">
        <!-- Replace with your Access Key -->
        <input type="hidden" name="access_key" value="{access_key}">

        <!-- Custom Form Inputs -->
        <label for="name">Name:</label>
        <input type="text" id="name" name="name" required><br>

        <label for="email">Email:</label>
        <input type="email" id="email" name="email" required><br>

        <label for="message">Message:</label>
        <textarea id="message" name="message" required></textarea><br>

        <button type="submit">Submit Form</button>
    </form>
    '''
    return render_template('form_template.html', form_html=form_html)

# Route for handling form submissions
@app.route('/submit', methods=['POST'])
def submit_form():
    access_key = request.form.get('access_key')
    user = User.query.filter_by(access_key=access_key).first()

    if not user:
        flash('Invalid Access Key', 'danger')
        return redirect(url_for('index'))

    # Capture form submission data
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']

    # Notify the admin about the form submission
    msg_admin = Message('New Form Submission', recipients=[app.config['MAIL_USERNAME']])
    msg_admin.body = f'New submission from {name} ({email}):\n\n{message}'
    mail.send(msg_admin)

    # Notify the user (form owner) about the new submission
    msg_user = Message('New Submission on Your Form', recipients=[user.email])
    msg_user.body = f'You have received a new submission from {name} ({email}):\n\n{message}'
    mail.send(msg_user)

    flash('Form submitted successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)
