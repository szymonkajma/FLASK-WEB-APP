from flask import Blueprint, render_template, request, flash, jsonify, send_file, redirect, url_for, session
from flask_login import login_required, current_user
from weasyprint import HTML

from . import db
from .models import Note, User

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if check_for_new_items(current_user):
        session['new_items'] = True
    else:
        session.pop('new_items', None)

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


@views.route('/share-note/', methods=['POST'])
def share_notes():
    selected_notes = request.form.getlist('selected_notes[]')
    username = request.form.get('username')
    share_with_user = User.query.filter_by(username=username).first()

    if not selected_notes:
        flash('No notes selected!', category='error')
        return redirect(url_for('views.home'))
    if not share_with_user:
        flash('Chose user to share with!', category='error')
        return redirect(url_for('views.home'))

    for note_id in selected_notes:
        note = Note.query.get(note_id)
        if note:
            if share_with_user not in note.shared_with:
                note.shared_with.append(share_with_user)
                db.session.add(note)
    
    db.session.commit()

    flash('Notes shared!', category='success')

    return redirect(url_for('views.home'))


@views.route('/add-note/', methods=['POST'])
def add_note():
    selected_notes = request.form.getlist('selected_notes[]')

    for note_id in selected_notes:
        note = Note.query.get(note_id)
        if note:
            current_user.notes.append(note)
            note.shared_with.remove(current_user)
            db.session.commit()

    flash('Notes added to your notes!', category='success')

    return redirect(url_for('views.home'))

@views.route('/download-note/', methods=['POST'])
def download_pdf():
    selected_notes = request.form.getlist('selected_notes[]')
    if not selected_notes:
        flash('No notes selected!', category='error')
        return redirect(url_for('views.home'))

    user_name = current_user.first_name
    body = join_notes(selected_notes, joiner="<br/><br/>")

    html_file_name = 'notatki1.html'

    with open(html_file_name, 'w') as file_html:
        file_html.write('''<html>
        <head>
        <meta charset="utf-8"/>
        </head>
        <body>
        <h2>Here are your notes, ''' + user_name + '''</h2>
        <p>''' + body + '''</p>
        </body>
        </html>''')

    pdf_file = "notatki1.pdf"
    HTML(html_file_name).write_pdf(pdf_file)

    flash('PDF downloading!', category='success')

    return send_file(f'../{pdf_file}', as_attachment=True)  # bardzo bym chciał żeby po tym strona się przeładowała


def join_notes(notes, joiner="</br>"):
    body = ""
    for note_id in notes:
        note = Note.query.get(note_id)
        if note:
            body += str(joiner) + str("<b>" + note.title + "</b></br>") + str(note.data)
    return body


def check_for_new_items(user):
    new_shared_notes = []
    for note in user.shared_notes:
        if note.date > user.last_checked_shared_notes_date:
            new_shared_notes.append(note)
    return len(new_shared_notes) > 0