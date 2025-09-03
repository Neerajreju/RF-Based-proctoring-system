from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import uuid
import threading
import time
import subprocess

app = Flask(__name__)
app.secret_key = 'secret'

# In-memory storage for exams and alerts
exam_sessions = {}  # token: {duration, sdr, name, email, alerts}
questions_db = {}  # token: [ {question, type, options, answer} ]
student_answers = {}  # token: [{ name, email, answers: {question: answer} }]



# Function to run proctoring tools
def run_proctoring(token, duration, sdr_enabled):
    end_time = time.time() + duration * 60

    def face_mobile_detection():
        subprocess.run(['python', 'the_fin.py', token])
        send_alert(token, "Face or Mobile detection triggered!")

    def run_sdr():
        subprocess.run(['python', 'sdr_script.py'])
        send_alert(token, "SDR detected anomalies!")

    threads = []

    t1 = threading.Thread(target=face_mobile_detection)
    t1.start()
    threads.append(t1)

    if sdr_enabled:
        t2 = threading.Thread(target=run_sdr)
        t2.start()
        threads.append(t2)

    # Store threads in session
    exam_sessions[token]['threads'] = threads

    # Wait until manually stopped or time expires
    while time.time() < end_time and not exam_sessions[token].get('stopped'):
        time.sleep(1)

    for t in threads:
        if t.is_alive():
            print(f"[INFO] Waiting for thread {t.name} to finish.")
            t.join()


    # Optional: Terminate threads or processes if needed
    for t in threads:
        t.join()

# Function to send alerts to the admin
def send_alert(token, alert):
    if token in exam_sessions:
        exam_sessions[token]['alerts'].append(alert)

@app.route('/')
def home():
    return redirect(url_for('admin_dashboard'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if request.method == 'POST':
        # Get exam settings from the form
        duration = int(request.form['duration'])
        sdr_enabled = 'sdr' in request.form
        token = str(uuid.uuid4())
        
        # Store exam session data
        exam_sessions[token] = {
            'duration': duration,
            'sdr': sdr_enabled,
            'alerts': [],
            'students': []
        }

        # Generate the full exam URL for sharing
        exam_url = request.host_url + 'exam/' + token  # This creates the full URL (with protocol)

        return render_template('admin_dashboard.html', token=token, sessions=exam_sessions, exam_url=exam_url)
    
    return render_template('admin_dashboard.html', token=None, sessions=exam_sessions)

@app.route('/exam/<token>', methods=['GET', 'POST'])
def exam_page(token):
    if token not in exam_sessions:
        return "Invalid exam link."
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        exam_sessions[token]['students'].append({'name': name, 'email': email})
        print("Students in token", token, "->", exam_sessions[token]['students'])

        session['token'] = token
        session['name'] = name
        session['email'] = email

        # Start proctoring tools in background
        threading.Thread(target=run_proctoring, args=(token, exam_sessions[token]['duration'], exam_sessions[token]['sdr'])).start()

        duration = exam_sessions[token]['duration']
        return render_template('student_exam.html', duration=duration, token=token, questions=questions_db.get(token, []))

    return render_template('student_login.html', token=token)


@app.route('/submit_answers/<token>', methods=['POST'])
def submit_answers(token):
    responses = {}
    for q in questions_db.get(token, []):
        responses[q['question']] = request.form.get(q['question'], '')

    student_entry = {
        'name': session['name'],
        'email': session['email'],
        'answers': responses
    }

    if token not in student_answers:
        student_answers[token] = []
    student_answers[token].append(student_entry)

    exam_sessions[token]['students'].append({
    'name': session['name'],
    'email': session['email'],
    'status': 'Submitted'
        })
    return redirect(url_for('view_report', token=token, email=session['email']))


# @app.route('/view_report/<token>')
# def view_report(token):
#     email = request.args.get('email')
#     students = student_answers.get(token, [])

#     for student in students:
#         if student['email'] == email:
#             qset = questions_db.get(token, [])
#             report = []

#             for q in qset:
#                 user_ans = student['answers'].get(q['question'], '')
#                 is_correct = False
#                 if q['type'] == 'mcq':
#                     is_correct = (user_ans.strip() == q['answer'].strip())
#                 else:
#                     is_correct = (user_ans.strip().lower() == q['answer'].strip().lower())

#                 report.append({
#                     'question': q['question'],
#                     'answer': user_ans,
#                     'correct': is_correct,
#                     'expected': q['answer']
#                 })

#             return render_template('report.html', report=report, student=student, token=token)

#     return "No report found for this email."

@app.route('/view_report/<token>')
def view_report(token):
    email = request.args.get('email')
    students = student_answers.get(token, [])

    for student in students:
        if student['email'] == email:
            qset = questions_db.get(token, [])
            report = []

            for q in qset:
                user_ans = student['answers'].get(q['question'], '')
                is_correct = False
                if q['type'] == 'mcq':
                    is_correct = (user_ans.strip() == q['answer'].strip())
                else:
                    is_correct = (user_ans.strip().lower() == q['answer'].strip().lower())

                report.append({
                    'question': q['question'],
                    'answer': user_ans,
                    'correct': is_correct,
                    'expected': q['answer']
                })

            # ✅ Extract alerts relevant to this student
            all_alerts = exam_sessions.get(token, {}).get('alerts', [])
            student_alerts = [
                alert for alert in all_alerts
                if student['name'] in alert or student['email'] in alert or 'student' in alert.lower()
            ]

            return render_template('report.html', report=report, student=student, token=token, alerts=student_alerts)

    return "No report found for this email."





@app.route('/submit_exam', methods=['POST'])
def submit_exam():
    data = request.json
    token = data.get('token')
    student_name = data.get('student_name')
    student_email = data.get('student_email')

    if token in exam_sessions:
        exam_sessions[token]['students'][-1]['status'] = "Submitted"
        exam_sessions[token]['alerts'].append(f"Exam submitted by {student_name} ({student_email})")

        # ✅ Stop the proctoring loop
        exam_sessions[token]['stopped'] = True

        return jsonify(message="Exam submitted successfully")
    
    return jsonify(message="Invalid token or session")


@app.route('/send_alert', methods=['POST'])
def send_alert_route():
    data = request.json
    token = data.get('token')
    alert = data.get('alert')

    if token in exam_sessions:
        exam_sessions[token]['alerts'].append(alert)
    
    return '', 204

@app.route('/alerts/<token>')
def view_alerts(token):
    if token in exam_sessions:
        return jsonify(alerts=exam_sessions[token]['alerts'])
    return jsonify(alerts=[])

@app.route('/create_question/<token>', methods=['GET', 'POST'])
def create_question(token):
    if request.method == 'POST':
        question = request.form['question']
        qtype = request.form['qtype']  # 'mcq' or 'text'
        options = request.form.getlist('options') if qtype == 'mcq' else []
        answer = request.form['answer']

        if token not in questions_db:
            questions_db[token] = []

        questions_db[token].append({
            'question': question,
            'type': qtype,
            'options': options,
            'answer': answer
        })
        return redirect(url_for('admin_dashboard'))

    return render_template('create_question.html', token=token)



if __name__ == '__main__':
    app.run(debug=True)
