from flask import Flask,render_template, redirect, url_for, session, flash, Response
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,DateField
from wtforms.validators import DataRequired, Email, ValidationError
import bcrypt
from camera import Video
import pymysql

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Jeeshan@87867'
app.config['MYSQL_DB'] = 'mini'
app.secret_key = 'your_secret_key_here'

def get_db_connection():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB'],
        cursorclass=pymysql.cursors.DictCursor
    )

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_email(self, field):
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email=%s", (field.data,))
            user = cursor.fetchone()
        connection.close()
        if user:
            raise ValidationError('Email Already Taken')

class RegisterForm_parti(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    usn = StringField("USN",validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_email(self, field):
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM participants WHERE email=%s", (field.data,))
            user = cursor.fetchone()
        connection.close()
        if user:
            raise ValidationError('Email Already Taken')

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


# Event Creation Form
class EventForm(FlaskForm):
    event_name = StringField('Event Name', validators=[DataRequired()])
    event_date = DateField('Event Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Create Event')

@app.route('/')
def index():
    # Render the main index.html file
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Store data into database
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                           (name, email, hashed_password))
        connection.commit()
        connection.close()

        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/participant_register', methods=['GET', 'POST'])
def participant_register():
    form = RegisterForm_parti()
    if form.validate_on_submit():
        name = form.name.data
        usn = form.usn.data
        email = form.email.data
        password = form.password.data

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Store data into database
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO participants (name,usn, email, password) VALUES (%s, %s, %s,%s)",
                           (name,usn, email, hashed_password))
        connection.commit()
        connection.close()

        return redirect(url_for('participant_login'))

    return render_template('participant_register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()
        connection.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        else:
            flash("Login failed. Please check your email and password")
            return redirect(url_for('login'))

    return render_template('login.html', form=form)


@app.route('/participant_login', methods=['GET', 'POST'])
def participant_login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM participants WHERE email=%s", (email,))
            participant = cursor.fetchone()
        connection.close()

        if participant and bcrypt.checkpw(password.encode('utf-8'), participant['password'].encode('utf-8')):
            session['participant_id'] = participant['id']
            return redirect(url_for('participant_dashboard'))
        else:
            flash("Login failed. Please check your email and password")
            return redirect(url_for('participant_login'))

    return render_template('participant_login.html', form=form)



@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user_id = session['user_id']

        # Connect to the database
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Fetch user details
            cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
            user = cursor.fetchone()

            # Fetch events created by the user or events that the user still needs to take
            cursor.execute("""
                SELECT * FROM events 
                WHERE user_id=%s AND event_status='created'
                ORDER BY event_date DESC
            """, (user_id,))
            events = cursor.fetchall()
        connection.close()

        if user:
            return render_template('dashboard.html', user_email=user['email'], events=events)

    return redirect(url_for('login'))


@app.route('/participant_dashboard')
def participant_dashboard():
    if 'participant_id' in session:  # Ensure participant is logged in
        participant_id = session['participant_id']

        # Connect to the database
        connection = get_db_connection()
        with connection.cursor() as cursor:

            # Fetch participant details
            cursor.execute("SELECT * FROM participants WHERE id=%s", (participant_id,))
            user = cursor.fetchone()

            # Fetch event details for the participant
            cursor.execute("""
                SELECT e.id, e.event_name, e.event_date
                FROM participations p
                JOIN events e ON p.event_id = e.id
                WHERE p.participant_id = %s
                ORDER BY e.event_date DESC
            """, (participant_id,))
            events = cursor.fetchall()

        connection.close()

        if user:  # If the participant exists in the database
            # Render the dashboard with event details
            return render_template(
                'participant_dashboard.html',
                user_email=user['email'],
                events=events
            )

    # Redirect to login if session is missing or participant not found
    return redirect(url_for('participant_login'))


@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    form = EventForm()

    if form.validate_on_submit():
        event_name = form.event_name.data
        event_date = form.event_date.data

        user_id = session.get('user_id')

        # Save the event to the databasee
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO events (user_id, event_name, event_date, event_status)
                VALUES (%s, %s, %s, 'created')
            """, (user_id, event_name, event_date))
            connection.commit()
        connection.close()

        return redirect(url_for('dashboard'))

    return render_template('create_event.html', form=form)


@app.route('/event_details/<int:event_id>')
def event_details(event_id):
    # Fetch the event details from the database using the event_id
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
        event = cursor.fetchone()

    # Check if the event exists
    if event is None:
        return "Event not found", 404

    connection.close()

    return render_template('event_details.html', event=event)


@app.route('/participant_event_details/<int:event_id>')
def participant_event_details(event_id):
    # Fetch the event details from the database using the event_id
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
        event = cursor.fetchone()

    # Check if the event exists
    if event is None:
        return "Event not found", 404

    connection.close()

    return render_template('participant_event_details.html', event=event)


@app.route('/remove_event/<int:event_id>', methods=['GET', 'POST'])
def remove_event(event_id):
    try:
        # Fetch the event details from the database using the event_id
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
            event = cursor.fetchone()

        # Check if the event exists
        if event is None:
            flash('Event not found', 'danger')  # Flash error message if the event doesn't exist
            return redirect(url_for('dashboard'))  # Redirect to dashboard if event is not found

        # If event exists, delete it from the database
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
            connection.commit()

        connection.close()

        return redirect(url_for('dashboard'))

    except Exception as e:
        flash(f'Error removing event: {str(e)}', 'danger')  # Flash error message if something goes wrong
        return redirect(url_for('dashboard'))


@app.route('/participant_remove_event/<int:event_id>', methods=['GET', 'POST'])
def participant_remove_event(event_id):
    if 'participant_id' in session:
        participant_id = session['participant_id']

        # Connect to the database
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Delete the participation record
            cursor.execute("""
                DELETE FROM participations
                WHERE participant_id = %s AND event_id = %s
            """, (participant_id, event_id))
            connection.commit()

        connection.close()

        return redirect(url_for('participant_dashboard'))
    else:
        return redirect(url_for('participant_login'))



@app.route('/start_event/<int:event_id>')
def strat_event(event_id):
    pass

@app.route('/events')
def events():
    if 'user_id' in session:
        user_id = session['user_id']

        # Connect to the database
        connection = get_db_connection()
        with connection.cursor() as cursor:

            # Fetch participant details for confirmation (optional)
            cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
            user = cursor.fetchone()

            # Fetch all events
            cursor.execute("""
                            SELECT e.id, e.event_name, e.event_date
                            FROM events e
                            ORDER BY e.event_date ASC
                        """)
            all_events = cursor.fetchall()

        connection.close()

        if user:
            # Render the events template with all available events
            return render_template(
                'events.html',
                user_email=user['email'],
                all_events=all_events
            )

    # Redirect to login if session is missing or participant not found
    return redirect(url_for('login'))


@app.route('/participant_events')
def participant_events():
    if 'participant_id' in session:
        participant_id = session['participant_id']

        # Connect to the database
        connection = get_db_connection()
        with connection.cursor() as cursor:

            # Fetch participant details for confirmation (optional)
            cursor.execute("SELECT * FROM participants WHERE id=%s", (participant_id,))
            user = cursor.fetchone()

            # Fetch all events the participant has not participated in
            cursor.execute("""
                SELECT e.id, e.event_name, e.event_date
                FROM events e
                WHERE e.id NOT IN (
                    SELECT p.event_id
                    FROM participations p
                    WHERE p.participant_id = %s
                )
                ORDER BY e.event_date ASC
            """, (participant_id,))
            available_events = cursor.fetchall()

        connection.close()

        if user:
            # Render the available events template
            return render_template(
                'participant_events.html',
                user_email=user['email'],
                available_events=available_events
            )

    # Redirect to login if session is missing or participant not found
    return redirect(url_for('participant_login'))


@app.route('/register_event/<int:event_id>')
def register_event(event_id):
    if 'participant_id' in session:
        participant_id = session['participant_id']

        # Connect to the database
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Insert a new record in the `participations` table
            cursor.execute("""
                INSERT INTO participations (participant_id, event_id)
                VALUES (%s, %s)
            """, (participant_id, event_id))
            connection.commit()

        connection.close()
        return redirect(url_for('participant_events'))

    # Redirect to login if session is missing
    return redirect(url_for('participant_login'))



@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/participant_logout')
def participant_logout():
    session.pop('user_id', None)
    return redirect(url_for('participant_login'))

def gen(camera):
    # Generate frames from the webcam
    while True:
        try:
            frame = camera.get_frame()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        except Exception as e:
            print(f"Error: {e}")
            break

@app.route('/video')
def video():
    # Stream video from the webcam
    return Response(gen(Video()), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/face_scanner')
def face_scanner():
    return render_template('face_scanner.html')

if __name__ == '__main__':
    # Run the Flask app
    app.run(host='192.168.246.125',port=5000,debug=True)
#ip 192.168.1.109
