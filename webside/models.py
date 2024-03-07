from datetime import datetime

from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


shared_notes = db.Table('shared_notes',
    db.Column('note_id', db.Integer, db.ForeignKey('note.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50))
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    shared_with = db.relationship('User', secondary=shared_notes, backref=db.backref('shared_notes', lazy='dynamic'))

    def share(self, user: "User", commit = False):
        if user in self.shared_with:
            return False

        self.shared_with.append(user)

        db.session.add(user)

        if commit:
            db.session.commit()

    @classmethod
    def from_note(cls, owner: "User", note: "Note"):
        return cls(title=note.title, data=note.data, date=note.date, user_id=owner.id)



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    notes = db.relationship('Note', backref='user')
    last_checked_shared_notes_date = db.Column(db.DateTime, default=func.now())

    def reset_last_checked(self):
        self.last_checked_shared_notes_date = datetime.utcnow()
        db.session.commit()

    def has_new_shared_notes(self):
        for note in self.shared_notes:
            if note.date > self.last_checked_shared_notes_date:
                return True
