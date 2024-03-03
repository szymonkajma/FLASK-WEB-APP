import smtplib

from flask import Blueprint, render_template, request, flash, jsonify, send_file, redirect, url_for
from flask_login import login_required, current_user
from weasyprint import HTML

from . import db
from .models import Note

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note = request.form.get('note')
        title = request.form.get('title')

        if len(title) < 1:
            title = "Note title"

        if len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Note(title=title, data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user)


@views.route('/note/<note_id>/delete/', methods=['POST'])
def delete_note(note_id):
    note = Note.query.get(note_id)

    if note and note.user_id == current_user.id:
        db.session.delete(note)
        db.session.commit()
        flash('Note deleted!', category='success')

    return redirect(url_for('views.home'))


@views.route('/send-note/', methods=['POST'])
def send_notes():
    selected_notes = request.args.get('selected_notes[]').split(',')
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


@views.route('/download-note/', methods=['POST'])
def download_pdf():
    selected_notes = request.form.getlist('selected_notes[]')
    user_name = current_user.first_name
    body = join_notes(selected_notes, joiner="<br/><br/>")

    html_file_name = 'notatki1.html'

    with open(html_file_name, 'w') as file_html:
        file_html.write('''<html>
        <head>
        </head>
        <body>
        <h2>Here are your notes, ''' + user_name + '''</h2>
        <p>''' + body + '''</p>
        </body>
        </html>''')

    pdf_file = "notatki1.pdf"
    HTML(html_file_name).write_pdf(pdf_file)

    flash('PDF downloading!', category='success')
    redirect(url_for('views.home'))

    return send_file(f'../{pdf_file}', as_attachment=True)

def join_notes(notes, joiner="</br>"):
    body = ""
    for note_id in notes:
        note = Note.query.get(note_id)
        if note:
            body += str(joiner) + str("<b>" + note.title + "</b></br>") + str(note.data)
    return body
