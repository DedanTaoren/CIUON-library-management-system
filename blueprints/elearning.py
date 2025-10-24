from flask import Blueprint, render_template, request, send_from_directory, flash, redirect, url_for
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, Video, Audio, ExamPaper, MarkingScheme, Announcement, StudentProgress, Student, User
from datetime import datetime
import os

elearning_bp = Blueprint('elearning', __name__, template_folder='../templates')


@elearning_bp.route('/login', methods=['GET', 'POST'])
def dukan_login():
    if current_user.is_authenticated:
        return redirect(url_for('elearning.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Welcome to Dukan E-Learning!', 'success')
            return redirect(url_for('elearning.index'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
    
    return render_template('elearning/dukan_login.html')


@elearning_bp.route('/signup', methods=['GET', 'POST'])
def dukan_signup():
    if current_user.is_authenticated:
        return redirect(url_for('elearning.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name', '')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('elearning/dukan_signup.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login instead.', 'error')
            return render_template('elearning/dukan_signup.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken. Please choose another.', 'error')
            return render_template('elearning/dukan_signup.html')
        
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role='student'
        )
        db.session.add(new_user)
        
        new_student = Student(
            name=full_name,
            email=email,
            student_number=username
        )
        db.session.add(new_student)
        
        try:
            db.session.commit()
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('elearning.dukan_login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
    
    return render_template('elearning/dukan_signup.html')


@elearning_bp.route('/logout')
@login_required
def dukan_logout():
    logout_user()
    flash('You have been logged out from Dukan.', 'info')
    return redirect(url_for('elearning.dukan_login'))


def log_progress(resource_type, resource_id, action='view'):
    if current_user.is_authenticated:
        student = Student.query.filter_by(email=current_user.email).first()
        if student:
            try:
                progress = StudentProgress(
                    student_id=student.id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=action
                )
                db.session.add(progress)
                db.session.commit()
            except Exception:
                db.session.rollback()


@elearning_bp.route('/')
@login_required
def index():
    recent_announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.created_at.desc()).limit(5).all()
    videos_count = Video.query.filter_by(is_active=True).count()
    audios_count = Audio.query.filter_by(is_active=True).count()
    exam_papers_count = ExamPaper.query.filter_by(is_active=True).count()
    marking_schemes_count = MarkingScheme.query.filter_by(is_active=True).count()
    
    recently_viewed = []
    student = Student.query.filter_by(email=current_user.email).first()
    if student:
        recent_progress = StudentProgress.query.filter_by(student_id=student.id).order_by(StudentProgress.accessed_at.desc()).limit(5).all()
        recently_viewed = recent_progress
    
    return render_template('elearning/index.html',
                         announcements=recent_announcements,
                         videos_count=videos_count,
                         audios_count=audios_count,
                         exam_papers_count=exam_papers_count,
                         marking_schemes_count=marking_schemes_count,
                         recently_viewed=recently_viewed)


@elearning_bp.route('/videos')
@login_required
def videos():
    hsk_level = request.args.get('level', '')
    search_query = request.args.get('search', '')
    
    query = Video.query.filter_by(is_active=True)
    
    if hsk_level:
        query = query.filter_by(hsk_level=hsk_level)
    
    if search_query:
        query = query.filter(Video.title.ilike(f'%{search_query}%'))
    
    all_videos = query.order_by(Video.created_at.desc()).all()
    
    return render_template('elearning/videos.html', videos=all_videos, current_level=hsk_level, search_query=search_query)


@elearning_bp.route('/videos/<int:video_id>')
@login_required
def video_detail(video_id):
    video = Video.query.get_or_404(video_id)
    if not video.is_active:
        flash('This video is no longer available.', 'warning')
        return redirect(url_for('elearning.videos'))
    log_progress('video', video_id, 'view')
    return render_template('elearning/video_detail.html', video=video)


@elearning_bp.route('/audios')
@login_required
def audios():
    hsk_level = request.args.get('level', '')
    exam_code = request.args.get('exam_code', '')
    
    query = Audio.query.filter_by(is_active=True)
    
    if hsk_level:
        query = query.filter_by(hsk_level=hsk_level)
    
    if exam_code:
        query = query.filter(Audio.exam_code.ilike(f'%{exam_code}%'))
    
    all_audios = query.order_by(Audio.created_at.desc()).all()
    
    return render_template('elearning/audios.html', audios=all_audios, current_level=hsk_level, exam_code=exam_code)


@elearning_bp.route('/audios/<int:audio_id>')
@login_required
def audio_detail(audio_id):
    audio = Audio.query.get_or_404(audio_id)
    if not audio.is_active:
        flash('This audio file is no longer available.', 'warning')
        return redirect(url_for('elearning.audios'))
    log_progress('audio', audio_id, 'view')
    return render_template('elearning/audio_detail.html', audio=audio)


@elearning_bp.route('/exam-papers')
@login_required
def exam_papers():
    hsk_level = request.args.get('level', '')
    exam_code = request.args.get('exam_code', '')
    year = request.args.get('year', '')
    
    query = ExamPaper.query.filter_by(is_active=True)
    
    if hsk_level:
        query = query.filter_by(hsk_level=hsk_level)
    
    if exam_code:
        query = query.filter(ExamPaper.exam_code.ilike(f'%{exam_code}%'))
    
    if year and year.isdigit():
        query = query.filter_by(exam_year=int(year))
    
    all_papers = query.order_by(ExamPaper.created_at.desc()).all()
    
    return render_template('elearning/exam_papers.html', 
                         exam_papers=all_papers, 
                         current_level=hsk_level, 
                         exam_code=exam_code,
                         year=year)


@elearning_bp.route('/exam-papers/<int:paper_id>')
@login_required
def exam_paper_detail(paper_id):
    paper = ExamPaper.query.get_or_404(paper_id)
    if not paper.is_active:
        flash('This exam paper is no longer available.', 'warning')
        return redirect(url_for('elearning.exam_papers'))
    log_progress('exam_paper', paper_id, 'view')
    return render_template('elearning/exam_paper_detail.html', paper=paper)


@elearning_bp.route('/exam-papers/<int:paper_id>/download')
@login_required
def download_exam_paper(paper_id):
    paper = ExamPaper.query.get_or_404(paper_id)
    if not paper.is_active:
        flash('This exam paper is no longer available.', 'warning')
        return redirect(url_for('elearning.exam_papers'))
    log_progress('exam_paper', paper_id, 'download')
    directory = os.path.dirname(paper.file_path)
    filename = os.path.basename(paper.file_path)
    return send_from_directory(directory, filename, as_attachment=True)


@elearning_bp.route('/marking-schemes')
@login_required
def marking_schemes():
    hsk_level = request.args.get('level', '')
    exam_code = request.args.get('exam_code', '')
    
    query = MarkingScheme.query.filter_by(is_active=True)
    
    if hsk_level:
        query = query.filter_by(hsk_level=hsk_level)
    
    if exam_code:
        query = query.filter(MarkingScheme.exam_code.ilike(f'%{exam_code}%'))
    
    all_schemes = query.order_by(MarkingScheme.created_at.desc()).all()
    
    return render_template('elearning/marking_schemes.html', 
                         marking_schemes=all_schemes, 
                         current_level=hsk_level, 
                         exam_code=exam_code)


@elearning_bp.route('/marking-schemes/<int:scheme_id>')
@login_required
def marking_scheme_detail(scheme_id):
    scheme = MarkingScheme.query.get_or_404(scheme_id)
    if not scheme.is_active:
        flash('This marking scheme is no longer available.', 'warning')
        return redirect(url_for('elearning.marking_schemes'))
    log_progress('marking_scheme', scheme_id, 'view')
    return render_template('elearning/marking_scheme_detail.html', scheme=scheme)


@elearning_bp.route('/marking-schemes/<int:scheme_id>/download')
@login_required
def download_marking_scheme(scheme_id):
    scheme = MarkingScheme.query.get_or_404(scheme_id)
    if not scheme.is_active:
        flash('This marking scheme is no longer available.', 'warning')
        return redirect(url_for('elearning.marking_schemes'))
    log_progress('marking_scheme', scheme_id, 'download')
    directory = os.path.dirname(scheme.file_path)
    filename = os.path.basename(scheme.file_path)
    return send_from_directory(directory, filename, as_attachment=True)


@elearning_bp.route('/announcements')
@login_required
def announcements():
    all_announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.created_at.desc()).all()
    return render_template('elearning/announcements.html', announcements=all_announcements)


@elearning_bp.route('/my-progress')
@login_required
def my_progress():
    student = Student.query.filter_by(email=current_user.email).first()
    
    if not student:
        flash('Student profile not found. Please contact the administrator.', 'warning')
        return redirect(url_for('elearning.index'))
    
    progress_records = StudentProgress.query.filter_by(student_id=student.id).order_by(StudentProgress.accessed_at.desc()).all()
    
    stats = {
        'videos_viewed': StudentProgress.query.filter_by(student_id=student.id, resource_type='video').count(),
        'audios_played': StudentProgress.query.filter_by(student_id=student.id, resource_type='audio').count(),
        'papers_viewed': StudentProgress.query.filter_by(student_id=student.id, resource_type='exam_paper', action='view').count(),
        'papers_downloaded': StudentProgress.query.filter_by(student_id=student.id, resource_type='exam_paper', action='download').count(),
        'schemes_viewed': StudentProgress.query.filter_by(student_id=student.id, resource_type='marking_scheme').count(),
    }
    
    return render_template('elearning/my_progress.html', progress_records=progress_records, stats=stats)


@elearning_bp.route('/search')
@login_required
def search():
    query_str = request.args.get('q', '')
    resource_type = request.args.get('type', 'all')
    
    results = {
        'videos': [],
        'audios': [],
        'exam_papers': [],
        'marking_schemes': []
    }
    
    if query_str:
        if resource_type in ['all', 'videos']:
            results['videos'] = Video.query.filter(
                Video.is_active == True,
                Video.title.ilike(f'%{query_str}%')
            ).all()
        
        if resource_type in ['all', 'audios']:
            results['audios'] = Audio.query.filter(
                Audio.is_active == True,
                (Audio.title.ilike(f'%{query_str}%') | Audio.exam_code.ilike(f'%{query_str}%'))
            ).all()
        
        if resource_type in ['all', 'exam_papers']:
            results['exam_papers'] = ExamPaper.query.filter(
                ExamPaper.is_active == True,
                (ExamPaper.title.ilike(f'%{query_str}%') | ExamPaper.exam_code.ilike(f'%{query_str}%'))
            ).all()
        
        if resource_type in ['all', 'marking_schemes']:
            results['marking_schemes'] = MarkingScheme.query.filter(
                MarkingScheme.is_active == True,
                (MarkingScheme.title.ilike(f'%{query_str}%') | MarkingScheme.exam_code.ilike(f'%{query_str}%'))
            ).all()
    
    return render_template('elearning/search_results.html', results=results, query=query_str, resource_type=resource_type)
