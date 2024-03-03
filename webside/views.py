from flask import Blueprint, render_template, request, flash, jsonify, send_file, redirect, url_for
from flask_login import login_required, current_user
from .models import Note
from . import db
import json
import smtplib
from weasyprint import HTML
#from flask_mail import Message

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note = request.form.get('note')

        if len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user)


@views.route('delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
            flash('Note deleted!', category='success')

    return jsonify({})


# tym sposobem udalo sie zachowac funkcjonalnosc checkboxsow zamiast dodawac przycisk do kazdej notatki
@views.route('/send-or-download-note', methods=['POST'])
def send_or_download_note():
    action = request.form.get('action')
    selected_notes = request.form.getlist('selected_notes[]')

    if action == 'send':
        return redirect(url_for('send_notes', selected_notes=','.join(selected_notes)))
    elif action == 'download':
        return redirect(url_for('download_pdf', selected_notes=','.join(selected_notes)))
    else:
        return jsonify({'error': 'Invalid action'})

@views.route('/send-note/', methods=['GET', 'POST'])
def send_notes():
    if request.method == 'POST':
        selected_notes = request.args.get('selected_notes').split(',')
        user_name = current_user.first_name
        subject = f'Here are your notes, {user_name}'
        user_mail = current_user.email

        body = join_notes(selected_notes, joiner="\n\n")

        # tu jest cos zjebane z konfiguracja serwera poczty, ale chyba przez to ze nie chcialem im zaplacic
        with smtplib.SMTP('live.smtp.mailtrap.io', 587) as smtp:
            smtp.login('api', 'e89b47ed2b2954dfb93f46e0444dd8ce')
            mail_contents = f'Subject: {subject}\n\n{body}'

            smtp.sendmail('mailtrap@demomailtrap.com', user_mail, mail_contents)

        flash('Notes sent!', category='success')  # to dziala dopiero po odswiezeniu i nie wiem czemu

    return jsonify({})

@views.route('/download-note/', methods=['GET', 'POST'])
def download_pdf():
    global pdf_path
    if request.method == 'POST':
        selected_notes = request.args.get('selected_notes').split(',')
        body = join_notes(selected_notes, joiner="<br/><br/>")

        # notatki do pliku html
        file_html = open("notatki1.html", "w")
        file_html.write('''<html>
        <head>
        <title>Your notes</title>
        </head>
        <body>
        <p>''' + body + '''</p>
        </body>
        </html>''')
        file_html.close()

        # konwersja html na PDF
        html_file = 'notatki1.html'
        pdf_file = 'notatki1.pdf'
        HTML(html_file).write_pdf(pdf_file)
        pdf_path = '/Users/szymonkajma/Downloads/FLASK-WEB-APP/notatki1.pdf'

        flash('PDF downloading!', category='success')

        return send_file(pdf_path, as_attachment=True)
    else:
        flash('No notes selected', category='error')
        return redirect(url_for('home.html'))


def join_notes(notes, joiner):
    body = ""
    for note_id in notes:
        note = Note.query.get(note_id)
        if note:
            note_data = note.data
            note_data = str(note_data)
            body = body + str(joiner) + note_data
    return body
