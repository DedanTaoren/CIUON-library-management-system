from app import create_app
from models import BorrowRecord, db
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    borrow = BorrowRecord.query.filter_by(returned_at=None).first()
    if borrow:
        borrow.due_date = datetime.utcnow() - timedelta(days=7)
        db.session.commit()
        print(f"Borrow record {borrow.id} is now overdue for testing.")
    else:
        print("No active borrow record found.")
