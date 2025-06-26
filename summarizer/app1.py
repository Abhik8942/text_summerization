from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from summarizer.text_summarizer import summarize_text
from summarizer.video_summarizer import transcribe_and_summarize
import pypyodbc as odbc
from passlib.hash import bcrypt
from datetime import datetime, timedelta
import os
import random
import smtplib
from email.mime.text import MIMEText
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key')

# Email Configuration
EMAIL_SENDER = 'abhik7585@gmail.com'
EMAIL_PASSWORD = 'xlyc bfkd oizd topn'  # Use App Password for Gmail

# Database and other previous configurations remain the same
DRIVER_NAME = 'SQL SERVER'
SERVER_NAME = r'ABHIK\SQLEXPRESS'
DATABASE_NAME = 'JJ'
connection_string = f"""
DRIVER={{SQL Server}};
SERVER={SERVER_NAME};
DATABASE={DATABASE_NAME};
Trusted_Connection=yes;
"""
def get_db_connection():
    try:
        conn = odbc.connect(connection_string)
        print("Database connected successfully!")
        return conn
    except odbc.Error as e:
        print("Failed to connect to database.")
        print(f"Error: {e}")
        return None
    
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
@app.route('/')
def home():
    username = session.get('username')
    return render_template('home.html', username=username)

# OTP Storage (in-memory, can be replaced with a database-backed solution)
otp_storage = {}

def send_otp_email(email, otp):
    try:
        msg = MIMEText(f'Your OTP is: {otp}. It will expire in 10 minutes.')
        msg['Subject'] = 'OTP for Registration'
        msg['From'] = EMAIL_SENDER
        msg['To'] = email

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False

@app.route('/send_otp', methods=['POST'])
def send_otp():
    email = request.form['email']
    otp = str(random.randint(100000, 999999))
    
    # Store OTP with expiration
    otp_storage[email] = {
        'otp': otp,
        'expires': datetime.now() + timedelta(minutes=10)
    }

    if send_otp_email(email, otp):
        return jsonify({"success": True, "message": "OTP sent successfully"})
    else:
        return jsonify({"success": False, "message": "Failed to send OTP"}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        
        # OTP verification
        if 'otp' in request.form:
            stored_otp = otp_storage.get(email)
            
            # Check OTP validity
            if not stored_otp or stored_otp['expires'] < datetime.now():
                return jsonify({"success": False, "message": "OTP expired. Please resend."}), 400
            
            if request.form['otp'] != stored_otp['otp']:
                return jsonify({"success": False, "message": "Invalid OTP"}), 400
            
            # OTP verified, proceed with registration
            hashed_password = bcrypt.hash(password)
            conn = get_db_connection()
            
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        INSERT INTO Users (FirstName, LastName, Username, Email, PhoneNumber, PasswordHash)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (first_name, last_name, username, email, phone, hashed_password))
                    conn.commit()
                    
                    # Clear OTP after successful registration
                    del otp_storage[email]
                    
                    return jsonify({"success": True, "message": "Registration successful! Please log in."})
                except odbc.Error as e:
                    return jsonify({"success": False, "message": f"Registration failed: {str(e)}"}), 400
                finally:
                    cursor.close()
                    conn.close()
            else:
                return jsonify({"success": False, "message": "Database connection failed."}), 500
        else:
            # Initial OTP request
            otp = str(random.randint(100000, 999999))
            
            # Store OTP with expiration
            otp_storage[email] = {
                'otp': otp,
                'expires': datetime.now() + timedelta(minutes=10)
            }
            
            if send_otp_email(email, otp):
                return jsonify({"success": True, "message": "OTP sent successfully"})
            else:
                return jsonify({"success": False, "message": "Failed to send OTP"}), 500
    
    return render_template('register.html')

# Rest of the previous code remains the same
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT UserID, PasswordHash, FirstName FROM Users WHERE Username = ?", (username,))
                user = cursor.fetchone()
                if user and bcrypt.verify(password, user[1]):
                    session['user_id'] = user[0]
                    session['username'] = user[2]
                    next_page = request.args.get('next') or url_for('home')
                    return jsonify({
                        "success": True,
                        "message": "Login successful!",
                        "username": user[2],  # Include the first name in the response
                        "redirect": next_page
                    })
                else:
                    return jsonify({
                        "success": False,
                        "message": "Invalid username or password!"
                    }), 401
            except odbc.Error as e:
                return jsonify({
                    "success": False,
                    "message": f"Login failed: {str(e)}"
                }), 500
            finally:
                cursor.close()
                conn.close()
        else:
            return jsonify({
                "success": False,
                "message": "Database connection failed."
            }), 500
    return render_template('login.html')
@app.route('/logout')
@login_required
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully!"})
@app.route('/summarize_text', methods=['GET', 'POST'])
@login_required
def text_summarize():
    if request.method == 'POST':
        input_text = request.form['text']
        try:
            summary = summarize_text(input_text)
            save_summarization_history('text', input_text, summary)
            return jsonify({
                'success': True,
                'summary': summary,
                'original_text': input_text
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    return render_template('summarize_text.html')
@app.route('/summarize_video', methods=['GET', 'POST'])
@login_required
def video_summarize():
    if request.method == 'POST':
        youtube_url = request.form['youtube_url']
        try:
            summary = transcribe_and_summarize(youtube_url)
            save_summarization_history('video', youtube_url, summary)
            return jsonify({
                'success': True,
                'summary': summary
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    return render_template('summarize_video.html')
@app.route('/summarize_website', methods=['GET', 'POST'])
@login_required
def website_summarize():
    if request.method == 'POST':
        website_url = request.form['website_url']
        try:
            from summarizer.website_summarizer import summarize_website
            summary = summarize_website(website_url)
            save_summarization_history('website', website_url, summary)
            return jsonify({
                'success': True,
                'summary': summary
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    return render_template('summarize_website.html')
def save_summarization_history(summary_type, original_content, summary):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO SummarizationHistory (UserID, SummaryType, OriginalContent, Summary, DateCreated)
                VALUES (?, ?, ?, ?, ?)
            """, (session['user_id'], summary_type, original_content, summary, datetime.now()))
            conn.commit()
        except odbc.Error as e:
            print(f"Error saving summarization history: {e}")
        finally:
            cursor.close()
            conn.close()
@app.route('/get_history')
@login_required
def get_history():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT HistoryID, SummaryType, OriginalContent, Summary, DateCreated
                FROM SummarizationHistory
                WHERE UserID = ?
                ORDER BY DateCreated DESC
            """, (session['user_id'],))
            history = cursor.fetchall()
            return render_template('history.html', history=[
                {
                    "HistoryID": h[0],
                    "SummaryType": h[1],
                    "OriginalContent": h[2],
                    "Summary": h[3],
                    "DateCreated": h[4].strftime("%d/%b/%Y %H:%M:%S")
                } for h in history
            ])
        except odbc.Error as e:
            return jsonify({
                "success": False,
                "message": f"Failed to fetch history: {str(e)}"
            }), 500
        finally:
            cursor.close()
            conn.close()
    else:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500
@app.route('/view_history/<int:history_id>')
@login_required
def view_history(history_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT SummaryType, OriginalContent, Summary, DateCreated
                FROM SummarizationHistory
                WHERE HistoryID = ? AND UserID = ?
            """, (history_id, session['user_id']))
            
            history_item = cursor.fetchone()
            
            if history_item:
                return render_template('historycontent.html', 
                    type=history_item[0],
                    content=history_item[1],
                    summary=history_item[2],
                    date=history_item[3].strftime("%d/%b/%Y %H:%M:%S")
                )
            else:
                return redirect(url_for('get_history'))
                
        except odbc.Error as e:
            print(f"Database error: {e}")
            return redirect(url_for('get_history'))
        finally:
            cursor.close()
            conn.close()
    return redirect(url_for('get_history'))

if __name__ == '__main__':
    app.run(debug=True)