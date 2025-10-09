from models import db, User, Category, Student, Staff, Book, BorrowRecord, Fine, AuditLog, BackupLog, NotificationPreference, EmailLog
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/confucius_library.db'
db.init_app(app)

with app.app_context():
    db.session.query(User).delete()
    db.session.query(Category).delete()
    db.session.query(Student).delete()
    db.session.query(Staff).delete()
    db.session.query(Book).delete()
    db.session.query(BorrowRecord).delete()
    db.session.query(Fine).delete()
    db.session.query(AuditLog).delete()
    db.session.query(BackupLog).delete()
    db.session.query(NotificationPreference).delete()
    db.session.query(EmailLog).delete()
    db.session.commit()

print('All data cleared. Tables and schema remain intact.')
