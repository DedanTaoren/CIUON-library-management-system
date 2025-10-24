from flask_login import login_required
from flask import Blueprint
borrowing_bp = Blueprint('borrowing', __name__)

@borrowing_bp.route('/confirm_return/<int:borrow_id>', methods=['POST'], endpoint='confirm_return')
@login_required
def confirm_return(borrow_id):
    borrow_record = BorrowRecord.query.get_or_404(borrow_id)
    if borrow_record.returned_at:
        flash('This book has already been returned', 'error')
        return redirect(url_for('borrowing.list_borrows'))
    borrow_record.returned_at = datetime.utcnow()
    db.session.commit()
    # Send email to student
    if borrow_record.student_id:
        student = Student.query.get(borrow_record.student_id)
        fine = Fine.query.filter_by(borrow_record_id=borrow_record.id, student_id=student.id).first()
        subject = f"Book Returned & Fine Paid - {borrow_record.book_ref.title}"
        body = f"Dear {student.name},\n\nYou have successfully paid a fine of KES {fine.amount} for late return.\nBook: {borrow_record.book_ref.title}\nReturned At: {borrow_record.returned_at.strftime('%Y-%m-%d %H:%M:%S')}\n\nThank you for using the library!\nConfucius Institute Library\nUniversity of Nairobi"
        from utils.email_service import send_email
        send_email(student.email, subject, body, 'return_and_fine_paid', student.id, borrow_record.id)
    flash('Book returned and fine payment confirmed. Email sent to student.', 'success')
    return redirect(url_for('borrowing.list_borrows'))
@borrowing_bp.route('/confirm_return/<int:borrow_id>', methods=['POST'])
@login_required
def confirm_return(borrow_id):
    borrow_record = BorrowRecord.query.get_or_404(borrow_id)
    if borrow_record.returned_at:
        flash('This book has already been returned', 'error')
        return redirect(url_for('borrowing.list_borrows'))
    borrow_record.returned_at = datetime.utcnow()
    db.session.commit()
    # Send email to student
    if borrow_record.student_id:
        student = Student.query.get(borrow_record.student_id)
        fine = Fine.query.filter_by(borrow_record_id=borrow_record.id, student_id=student.id).first()
        subject = f"Book Returned & Fine Paid - {borrow_record.book_ref.title}"
        body = f"Dear {student.name},\n\nYou have successfully paid a fine of KES {fine.amount} for late return.\nBook: {borrow_record.book_ref.title}\nReturned At: {borrow_record.returned_at.strftime('%Y-%m-%d %H:%M:%S')}\n\nThank you for using the library!\nConfucius Institute Library\nUniversity of Nairobi"
        from utils.email_service import send_email
        send_email(student.email, subject, body, 'return_and_fine_paid', student.id, borrow_record.id)
    flash('Book returned and fine payment confirmed. Email sent to student.', 'success')
    return redirect(url_for('borrowing.list_borrows'))
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import Book, Student, Staff, BorrowRecord, Fine, db
from datetime import datetime, timedelta
from utils.audit_logger import log_action
from utils.email_service import send_email, send_due_date_reminders, send_overdue_notices

borrowing_bp = Blueprint('borrowing', __name__)

@borrowing_bp.route('/')
@login_required
def list_borrows():
    status = request.args.get('status', 'active')
    # ... existing code ...

@borrowing_bp.route('/fines/<int:fine_id>/pay', methods=['GET', 'POST'])
@login_required
def pay_fine_page(fine_id):
    fine = Fine.query.get_or_404(fine_id)
    student = Student.query.get(fine.student_id)
    if request.method == 'POST':
        # Here you would integrate with M-Pesa API and verify payment
        # For now, mark as paid for demonstration
        fine.paid = True
        fine.paid_at = datetime.utcnow()
        db.session.commit()
        flash('Fine paid successfully. Book return completed.', 'success')
        return redirect(url_for('borrowing.list_borrows'))
    return render_template('borrowing/pay_fine.html', fine=fine, student=student)
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import Book, Student, Staff, BorrowRecord, Fine, db
from datetime import datetime, timedelta
from utils.audit_logger import log_action
from utils.email_service import send_email, send_due_date_reminders, send_overdue_notices

borrowing_bp = Blueprint('borrowing', __name__)

@borrowing_bp.route('/')
@login_required
def list_borrows():
    status = request.args.get('status', 'active')
    
    if status == 'active':
        borrows = BorrowRecord.query.filter_by(returned_at=None).order_by(BorrowRecord.borrowed_at.desc()).all()
    elif status == 'returned':
        borrows = BorrowRecord.query.filter(BorrowRecord.returned_at.isnot(None)).order_by(BorrowRecord.returned_at.desc()).all()
    elif status == 'overdue':
        borrows = BorrowRecord.query.filter(
            BorrowRecord.returned_at.is_(None),
            BorrowRecord.due_date < datetime.utcnow()
        ).all()
    else:
        borrows = BorrowRecord.query.order_by(BorrowRecord.borrowed_at.desc()).all()
    
    return render_template('borrowing/list.html', borrows=borrows, status=status)

@borrowing_bp.route('/borrow', methods=['GET', 'POST'])
@login_required
def borrow_book():
    if request.method == 'POST':
        book_id = request.form['book_id']
        borrower_type = request.form['borrower_type']
        student_id = request.form.get('student_id') if borrower_type == 'student' else None
        staff_id = request.form.get('staff_id') if borrower_type == 'staff' else None
        book = Book.query.get_or_404(book_id)

        # Check availability
        if book.available_copies <= 0:
            flash('This book is not available for borrowing', 'error')
            return redirect(url_for('borrowing.list_borrows'))

        # Check student borrowing limits
        if student_id:
            student = Student.query.get_or_404(student_id)
            if student.current_borrowed_count >= 3:
                flash('Student has reached the maximum borrowing limit of 3 books', 'error')
                return redirect(url_for('borrowing.list_borrows'))

        # Create borrow record
        borrow_record = BorrowRecord(
            book_id=book_id,
            student_id=student_id,
            staff_id=staff_id,
            notes=request.form.get('notes', '')
        )

        try:
            db.session.add(borrow_record)
            db.session.commit()
            if student_id:
                borrower_name = student.name
                student_email = student.email
                borrow_date = borrow_record.borrowed_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(borrow_record, 'borrowed_at') and borrow_record.borrowed_at else datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                due_date = borrow_record.due_date.strftime('%Y-%m-%d') if hasattr(borrow_record, 'due_date') and borrow_record.due_date else (datetime.utcnow() + timedelta(days=4)).strftime('%Y-%m-%d')
                subject = f"Library Book Borrowed - {book.title}"
                body = f"Dear {borrower_name},\n\nYou have successfully borrowed the following book from the Confucius Institute Library:\n\nBook: {book.title}\nAuthor: {book.author or 'N/A'}\nBorrow Date: {borrow_date}\nDue Date: {due_date}\nMaximum Days Allowed: 4 days\n\nPlease return the book on or before the due date to avoid penalties.\n\nThank you,\nConfucius Institute Library\nUniversity of Nairobi"
                send_email(student_email, subject, body, 'borrowed', student.id, borrow_record.id)
            elif staff_id:
                staff_member = Staff.query.get_or_404(staff_id)
                borrower_name = staff_member.name
                staff_email = staff_member.email
                borrow_date = borrow_record.borrowed_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(borrow_record, 'borrowed_at') and borrow_record.borrowed_at else datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                subject = f"Library Book Borrowed - {book.title}"
                body = f"Dear {borrower_name},\n\nYou have successfully borrowed the following book from the Confucius Institute Library:\n\nBook: {book.title}\nAuthor: {book.author or 'N/A'}\nBorrow Date: {borrow_date}\n\nPlease return the book when you are done reading.\n\nThank you,\nConfucius Institute Library\nUniversity of Nairobi"
                send_email(staff_email, subject, body, 'borrowed', staff_member.id, borrow_record.id)
            else:
                borrower_name = 'Unknown'
            flash(f'Book "{book.title}" successfully borrowed by {borrower_name}', 'success')
            return redirect(url_for('borrowing.list_borrows'))
        except Exception as e:
            db.session.rollback()
            flash('Error processing borrow request', 'error')
            return redirect(url_for('borrowing.list_borrows'))
    # Only render the form for GET requests
    students = Student.query.order_by(Student.name).all()
    staff = Staff.query.order_by(Staff.name).all()
    all_books = Book.query.order_by(Book.title).all()
    books = [book for book in all_books if book.available_copies > 0]
    return render_template('borrowing/borrow_form.html', students=students, staff=staff, books=books)
            
@borrowing_bp.route('/return/<int:borrow_id>', methods=['GET', 'POST'])
@login_required
def return_book(borrow_id):
    borrow_record = BorrowRecord.query.get_or_404(borrow_id)
    
    if borrow_record.returned_at:
        flash('This book has already been returned', 'error')
        return redirect(url_for('borrowing.list_borrows'))
    
    if request.method == 'POST':
        # Check if overdue
        is_overdue = borrow_record.is_overdue
        borrow_record.returned_at = datetime.utcnow()
        borrow_record.notes = request.form.get('notes', borrow_record.notes)
        fine = None
        if is_overdue and borrow_record.student_id:
            # Calculate fine amount (40 KES per day overdue)
            days_overdue = borrow_record.days_overdue
            fine_amount = days_overdue * 40
            # Create fine if not already exists
            fine = Fine.query.filter_by(borrow_record_id=borrow_record.id, student_id=borrow_record.student_id).first()
            if not fine:
                fine = Fine(
                    student_id=borrow_record.student_id,
                    borrow_record_id=borrow_record.id,
                    amount=fine_amount,
                    reason=f"Late return: {days_overdue} days overdue",
                )
                db.session.add(fine)
        try:
            db.session.commit()
            # Send return confirmation email
            if borrow_record.student_id:
                student = Student.query.get(borrow_record.student_id)
                subject = f"Book Returned - {borrow_record.book_ref.title}"
                body = f"Dear {student.name},\n\nYou have successfully returned the book:\n\nBook: {borrow_record.book_ref.title}\nAuthor: {borrow_record.book_ref.author or 'N/A'}\nReturned At: {borrow_record.returned_at.strftime('%Y-%m-%d %H:%M:%S')}\n\nThank you for using the library!\nConfucius Institute Library\nUniversity of Nairobi"
                from utils.email_service import send_email
                send_email(student.email, subject, body, 'return_confirmation', student.id, borrow_record.id)
            elif borrow_record.staff_id:
                staff = Staff.query.get(borrow_record.staff_id)
                subject = f"Book Returned - {borrow_record.book_ref.title}"
                body = f"Dear {staff.name},\n\nYou have successfully returned the book:\n\nBook: {borrow_record.book_ref.title}\nAuthor: {borrow_record.book_ref.author or 'N/A'}\nReturned At: {borrow_record.returned_at.strftime('%Y-%m-%d %H:%M:%S')}\n\nThank you for using the library!\nConfucius Institute Library\nUniversity of Nairobi"
                from utils.email_service import send_email
                send_email(staff.email, subject, body, 'return_confirmation', staff.id, borrow_record.id)
            if is_overdue and fine:
                flash(f'This book was overdue. Fine of KES {fine.amount} must be paid.', 'warning')
                return redirect(url_for('borrowing.pay_fine_page', fine_id=fine.id))
            else:
                flash('Book returned successfully', 'success')
                return redirect(url_for('borrowing.list_borrows'))
        except Exception as e:
            db.session.rollback()
            flash('Error processing return', 'error')
    # Ensure fine exists for overdue books before rendering form
    if borrow_record.is_overdue and borrow_record.student_id:
        fine = Fine.query.filter_by(borrow_record_id=borrow_record.id, student_id=borrow_record.student_id).first()
        if not fine:
            days_overdue = borrow_record.days_overdue
            fine_amount = days_overdue * 40
            fine = Fine(
                student_id=borrow_record.student_id,
                borrow_record_id=borrow_record.id,
                amount=fine_amount,
                reason=f"Late return: {days_overdue} days overdue",
            )
            db.session.add(fine)
            db.session.commit()
    return render_template('borrowing/return_form.html', borrow_record=borrow_record)

@borrowing_bp.route('/fines')
@login_required
def list_fines():
    fines = Fine.query.filter_by(paid=False).order_by(Fine.created_at.desc()).all()
    return render_template('borrowing/fines.html', fines=fines)

@borrowing_bp.route('/fines/<int:fine_id>/pay', methods=['GET', 'POST'])
@login_required
def pay_fine(fine_id):
    fine = Fine.query.get_or_404(fine_id)
    student = Student.query.get(fine.student_id)
    from os import getenv
    confucius_number = getenv('CONFUCIUS_MPESA_NUMBER', '0748299301')
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        if phone_number and phone_number != student.phone:
            student.phone = phone_number
            db.session.commit()
        fine.paid = True
        fine.paid_at = datetime.utcnow()
        db.session.commit()
        flash(f'Fine paid successfully for phone number {phone_number}. Book return completed.', 'success')
        return redirect(url_for('borrowing.list_borrows'))
    return render_template('borrowing/pay_fine.html', fine=fine, student=student, confucius_number=confucius_number)