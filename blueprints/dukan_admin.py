from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Video, Audio, ExamPaper, MarkingScheme, Announcement
from functools import wraps
import os

dukan_admin_bp = Blueprint('dukan_admin', __name__, template_folder='../templates')

ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg'}
ALLOWED_PDF_EXTENSIONS = {'pdf'}
UPLOAD_FOLDER = 'static/uploads'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You need administrator privileges to access this page.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


@dukan_admin_bp.route('/')
@login_required
@admin_required
def index():
    videos_count = Video.query.filter_by(is_active=True).count()
    audios_count = Audio.query.filter_by(is_active=True).count()
    exam_papers_count = ExamPaper.query.filter_by(is_active=True).count()
    marking_schemes_count = MarkingScheme.query.filter_by(is_active=True).count()
    announcements_count = Announcement.query.filter_by(is_active=True).count()
    
    return render_template('dukan_admin/index.html',
                         videos_count=videos_count,
                         audios_count=audios_count,
                         exam_papers_count=exam_papers_count,
                         marking_schemes_count=marking_schemes_count,
                         announcements_count=announcements_count)


@dukan_admin_bp.route('/videos')
@login_required
@admin_required
def videos():
    all_videos = Video.query.filter_by(is_active=True).order_by(Video.created_at.desc()).all()
    return render_template('dukan_admin/videos.html', videos=all_videos)


@dukan_admin_bp.route('/videos/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_video():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        video_url = request.form.get('video_url')
        hsk_level = request.form.get('hsk_level')
        video_type = request.form.get('video_type', 'youtube')
        thumbnail_url = request.form.get('thumbnail_url')
        duration = request.form.get('duration')
        
        if not title or not video_url:
            flash('Title and video URL are required.', 'danger')
            return redirect(url_for('dukan_admin.add_video'))
        
        video = Video(
            title=title,
            description=description,
            video_url=video_url,
            hsk_level=hsk_level,
            video_type=video_type,
            thumbnail_url=thumbnail_url,
            duration=duration,
            created_by=current_user.id
        )
        
        db.session.add(video)
        db.session.commit()
        flash('Video added successfully!', 'success')
        return redirect(url_for('dukan_admin.videos'))
    
    return render_template('dukan_admin/add_video.html')


@dukan_admin_bp.route('/videos/<int:video_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_video(video_id):
    video = Video.query.get_or_404(video_id)
    
    if request.method == 'POST':
        video.title = request.form.get('title')
        video.description = request.form.get('description')
        video.video_url = request.form.get('video_url')
        video.hsk_level = request.form.get('hsk_level')
        video.video_type = request.form.get('video_type', 'youtube')
        video.thumbnail_url = request.form.get('thumbnail_url')
        video.duration = request.form.get('duration')
        
        db.session.commit()
        flash('Video updated successfully!', 'success')
        return redirect(url_for('dukan_admin.videos'))
    
    return render_template('dukan_admin/add_video.html', video=video)


@dukan_admin_bp.route('/videos/<int:video_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_video(video_id):
    video = Video.query.get_or_404(video_id)
    video.is_active = False
    db.session.commit()
    flash('Video deleted successfully!', 'success')
    return redirect(url_for('dukan_admin.videos'))


@dukan_admin_bp.route('/audios')
@login_required
@admin_required
def audios():
    all_audios = Audio.query.filter_by(is_active=True).order_by(Audio.created_at.desc()).all()
    return render_template('dukan_admin/audio.html', audios=all_audios)


@dukan_admin_bp.route('/audios/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_audio():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        exam_code = request.form.get('exam_code')
        hsk_level = request.form.get('hsk_level')
        duration = request.form.get('duration')
        
        audio_file = request.files.get('audio_file')
        transcript_file = request.files.get('transcript_file')
        
        if not title or not exam_code or not audio_file:
            flash('Title, exam code, and audio file are required.', 'danger')
            return redirect(url_for('dukan_admin.add_audio'))
        
        if audio_file and allowed_file(audio_file.filename, ALLOWED_AUDIO_EXTENSIONS):
            filename = secure_filename(audio_file.filename)
            audio_path = os.path.join(UPLOAD_FOLDER, 'audios', filename)
            os.makedirs(os.path.dirname(audio_path), exist_ok=True)
            audio_file.save(audio_path)
            
            transcript_path = None
            if transcript_file and allowed_file(transcript_file.filename, ALLOWED_PDF_EXTENSIONS):
                transcript_filename = secure_filename(transcript_file.filename)
                transcript_path = os.path.join(UPLOAD_FOLDER, 'transcripts', transcript_filename)
                os.makedirs(os.path.dirname(transcript_path), exist_ok=True)
                transcript_file.save(transcript_path)
            
            audio = Audio(
                title=title,
                description=description,
                exam_code=exam_code,
                hsk_level=hsk_level,
                file_path=audio_path,
                transcript_path=transcript_path,
                duration=duration,
                created_by=current_user.id
            )
            
            db.session.add(audio)
            db.session.commit()
            flash('Audio added successfully!', 'success')
            return redirect(url_for('dukan_admin.audios'))
        else:
            flash('Invalid audio file format. Allowed formats: mp3, wav, m4a, ogg', 'danger')
    
    return render_template('dukan_admin/add_audio.html')


@dukan_admin_bp.route('/audios/<int:audio_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_audio(audio_id):
    audio = Audio.query.get_or_404(audio_id)
    audio.is_active = False
    db.session.commit()
    flash('Audio deleted successfully!', 'success')
    return redirect(url_for('dukan_admin.audios'))


@dukan_admin_bp.route('/exam-papers')
@login_required
@admin_required
def exam_papers():
    all_papers = ExamPaper.query.filter_by(is_active=True).order_by(ExamPaper.created_at.desc()).all()
    return render_template('dukan_admin/pdfs.html', exam_papers=all_papers)


@dukan_admin_bp.route('/exam-papers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_exam_paper():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        exam_code = request.form.get('exam_code')
        hsk_level = request.form.get('hsk_level')
        exam_year = request.form.get('exam_year')
        audio_id = request.form.get('audio_id')
        
        pdf_file = request.files.get('pdf_file')
        
        if not title or not exam_code or not hsk_level or not pdf_file:
            flash('Title, exam code, HSK level, and PDF file are required.', 'danger')
            return redirect(url_for('dukan_admin.add_exam_paper'))
        
        if pdf_file and allowed_file(pdf_file.filename, ALLOWED_PDF_EXTENSIONS):
            filename = secure_filename(pdf_file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, 'exam_papers', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            pdf_file.save(file_path)
            
            exam_paper = ExamPaper(
                title=title,
                description=description,
                exam_code=exam_code,
                hsk_level=hsk_level,
                file_path=file_path,
                audio_id=int(audio_id) if audio_id else None,
                exam_year=int(exam_year) if exam_year else None,
                created_by=current_user.id
            )
            
            db.session.add(exam_paper)
            db.session.commit()
            flash('Exam paper added successfully!', 'success')
            return redirect(url_for('dukan_admin.exam_papers'))
        else:
            flash('Invalid file format. Only PDF files are allowed.', 'danger')
    
    audios = Audio.query.filter_by(is_active=True).all()
    return render_template('dukan_admin/add_pdf.html', audios=audios, type='exam_paper')


@dukan_admin_bp.route('/exam-papers/<int:paper_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_exam_paper(paper_id):
    paper = ExamPaper.query.get_or_404(paper_id)
    paper.is_active = False
    db.session.commit()
    flash('Exam paper deleted successfully!', 'success')
    return redirect(url_for('dukan_admin.exam_papers'))


@dukan_admin_bp.route('/marking-schemes')
@login_required
@admin_required
def marking_schemes():
    all_schemes = MarkingScheme.query.filter_by(is_active=True).order_by(MarkingScheme.created_at.desc()).all()
    return render_template('dukan_admin/marking_schemes.html', marking_schemes=all_schemes)


@dukan_admin_bp.route('/marking-schemes/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_marking_scheme():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        exam_code = request.form.get('exam_code')
        hsk_level = request.form.get('hsk_level')
        
        pdf_file = request.files.get('pdf_file')
        
        if not title or not exam_code or not hsk_level or not pdf_file:
            flash('Title, exam code, HSK level, and PDF file are required.', 'danger')
            return redirect(url_for('dukan_admin.add_marking_scheme'))
        
        if pdf_file and allowed_file(pdf_file.filename, ALLOWED_PDF_EXTENSIONS):
            filename = secure_filename(pdf_file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, 'marking_schemes', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            pdf_file.save(file_path)
            
            marking_scheme = MarkingScheme(
                title=title,
                description=description,
                exam_code=exam_code,
                hsk_level=hsk_level,
                file_path=file_path,
                created_by=current_user.id
            )
            
            db.session.add(marking_scheme)
            db.session.commit()
            
            exam_paper = ExamPaper.query.filter_by(exam_code=exam_code, is_active=True).first()
            if exam_paper:
                exam_paper.marking_scheme_id = marking_scheme.id
                db.session.commit()
            
            flash('Marking scheme added successfully!', 'success')
            return redirect(url_for('dukan_admin.marking_schemes'))
        else:
            flash('Invalid file format. Only PDF files are allowed.', 'danger')
    
    return render_template('dukan_admin/add_pdf.html', type='marking_scheme')


@dukan_admin_bp.route('/marking-schemes/<int:scheme_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_marking_scheme(scheme_id):
    scheme = MarkingScheme.query.get_or_404(scheme_id)
    scheme.is_active = False
    db.session.commit()
    flash('Marking scheme deleted successfully!', 'success')
    return redirect(url_for('dukan_admin.marking_schemes'))


@dukan_admin_bp.route('/announcements')
@login_required
@admin_required
def announcements():
    all_announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.created_at.desc()).all()
    return render_template('dukan_admin/announcements.html', announcements=all_announcements)


@dukan_admin_bp.route('/announcements/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_announcement():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        announcement_type = request.form.get('announcement_type', 'general')
        priority = request.form.get('priority', 'normal')
        
        if not title or not content:
            flash('Title and content are required.', 'danger')
            return redirect(url_for('dukan_admin.add_announcement'))
        
        announcement = Announcement(
            title=title,
            content=content,
            announcement_type=announcement_type,
            priority=priority,
            created_by=current_user.id
        )
        
        db.session.add(announcement)
        db.session.commit()
        flash('Announcement added successfully!', 'success')
        return redirect(url_for('dukan_admin.announcements'))
    
    return render_template('dukan_admin/add_announcement.html')


@dukan_admin_bp.route('/announcements/<int:announcement_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    announcement.is_active = False
    db.session.commit()
    flash('Announcement deleted successfully!', 'success')
    return redirect(url_for('dukan_admin.announcements'))
