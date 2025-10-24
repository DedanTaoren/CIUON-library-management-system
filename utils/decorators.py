from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def library_access_required(f):
    """
    Decorator to restrict access to library system routes.
    Only allows admin and librarian roles.
    Students (who signed up through Dukan) are redirected to Dukan.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if current_user.role == 'student':
            flash('This section is for library staff only. Students can access Dukan E-Learning.', 'info')
            return redirect(url_for('elearning.index'))
        
        return f(*args, **kwargs)
    return decorated_function
