import os
import io
import json
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, 
    flash, session, jsonify, send_file, abort
)
from werkzeug.utils import secure_filename

from config import Config
from database import (
    init_db, create_user, authenticate_user, get_user_by_id,
    save_summary_record, get_user_summaries, get_summary_by_id, delete_summary
)
from summarizer.nlp_preprocessor import LegalNLPPreprocessor
from summarizer.ocr_parser import DocumentParser
from summarizer.extractive_engine import HybridExtractiveSummarizer
from summarizer.report_generator import LegalReportGenerator

from summarizer.risk_annotator import RiskFactorAnnotator

app = Flask(__name__)
app.config.from_object(Config)

# Ensure required folders exist
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.REPORT_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)

# Initialize database
init_db()

# Initialize core services
parser = DocumentParser()
nlp = LegalNLPPreprocessor()
summarizer_engine = HybridExtractiveSummarizer()
report_gen = LegalReportGenerator()

risk_annotator = RiskFactorAnnotator()

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session and not session.get('is_guest', False):
            flash('Please log in or proceed as a guest to access the legal dashboard.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# Context processor for templates
@app.context_processor
def inject_user():
    return {
        'current_user': session.get('username', None),
        'is_guest': session.get('is_guest', False),
        'user_full_name': session.get('full_name', 'Guest User'),
        'current_year': datetime.now().year
    }

# ----------------- ROUTES ----------------- #

@app.route('/')
def index():
    """Official portal homepage with animated legal graphics and showcase."""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        
        user = authenticate_user(identifier, password)
        if user:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name'] or user['username']
            session['is_guest'] = False
            flash(f"Welcome back, {session['full_name']}!", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid legal credential or password. Please verify.", "danger")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        organization = request.form.get('organization', '').strip()

        if len(username) < 3:
            flash("Username must be at least 3 characters.", "danger")
            return render_template('register.html')
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template('register.html')

        success, res = create_user(username, email, password, full_name, organization)
        if success:
            flash("Legal practitioner account successfully registered. Please log in.", "success")
            return redirect(url_for('login'))
        else:
            flash(f"Registration failed: {res}", "danger")

    return render_template('register.html')

@app.route('/guest')
def guest_mode():
    """Enables instant Guest Mode access without credentials."""
    session.clear()
    session['user_id'] = None
    session['username'] = 'Guest Counsel'
    session['full_name'] = 'Guest Practitioner'
    session['is_guest'] = True
    flash("Browsing in Official Guest Mode. All legal analytics features are active.", "info")
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have successfully signed out of the Legal Portal.", "info")
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main legal document summarization workroom."""
    return render_template('dashboard.html')

@app.route('/analyze', methods=['POST'])
@login_required
def analyze_document():
    """Performs full OCR/extraction, NLP preprocessing, and extractive summarization."""
    raw_text = ""
    filename = "Pasted_Legal_Instrument.txt"
    doc_type = "Direct Text Input"
    method_used = "Manual Input"
    page_count = 1

    ratio = float(request.form.get('summary_ratio', Config.DEFAULT_SUMMARY_RATIO))
    algorithm = request.form.get('algorithm', 'hybrid')
    force_ocr = request.form.get('force_ocr') == 'on'

    # Check for file upload
    if 'document_file' in request.files and request.files['document_file'].filename:
        file = request.files['document_file']
        if allowed_file(file.filename):
            sec_name = secure_filename(file.filename)
            filename = sec_name
            save_path = os.path.join(Config.UPLOAD_FOLDER, sec_name)
            file.save(save_path)
            
            # Determine format
            ext = sec_name.rsplit('.', 1)[1].lower()
            if ext == 'pdf':
                doc_type = "PDF Legal Brief"
            elif ext == 'docx':
                doc_type = "Word Legal Contract"
            elif ext in ['png', 'jpg', 'jpeg', 'tiff', 'bmp']:
                doc_type = "Scanned Legal Affidavit / Image"
            else:
                doc_type = "Legal Text Document"

            try:
                raw_text, method_used, page_count = parser.parse_file(save_path, force_ocr=force_ocr)
            except Exception as e:
                flash(f"Error reading legal file: {str(e)}", "danger")
                return redirect(url_for('dashboard'))
        else:
            flash("Unsupported file extension. Allowed: PDF, DOCX, TXT, PNG, JPG.", "danger")
            return redirect(url_for('dashboard'))
    else:
        # Check pasted text
        raw_text = request.form.get('document_text', '').strip()
        if not raw_text:
            flash("Please either upload a document file or paste legal text to proceed.", "warning")
            return redirect(url_for('dashboard'))

    if len(raw_text.strip()) < 50:
        flash("The document contains insufficient readable text for extractive analysis.", "danger")
        return redirect(url_for('dashboard'))

    # Run Extractive Summarizer
    results = summarizer_engine.summarize(raw_text, ratio=ratio, algorithm=algorithm)
    results['filename'] = filename
    results['doc_type'] = doc_type
    results['method_used'] = method_used
    results['page_count'] = page_count
    results['algorithm_used'] = algorithm.capitalize()

    # Save to history database (supports both registered users and guest sessions)
    user_id = session.get('user_id')
    record_id = save_summary_record(
        user_id=user_id,
        filename=filename,
        doc_type=doc_type,
        orig_words=results['original_words'],
        sum_words=results['summary_words'],
        accuracy=results['accuracy_score'],
        compression=results['compression_ratio'],
        risk_level=results['risk_analysis'].get('level', 'Low'),
        risk_score=results['risk_analysis'].get('score', 0),
        clauses=results['clauses'],
        legalese=results['legalese'],
        summary_text=results['summary_text'],
        preview_text=raw_text
    )
    results['record_id'] = record_id

    # Store current result in session for quick re-export
    session['last_summary'] = results

    return render_template('result.html', result=results)

@app.route('/summary/<int:summary_id>')
@login_required
def view_summary(summary_id):
    """Retrieves an archived legal summary by ID."""
    rec = get_summary_by_id(summary_id)
    if not rec:
        flash("Summary record not found or inaccessible.", "danger")
        return redirect(url_for('history'))

    # Reconstruct result structure
    sum_sentences = [s.strip() for s in rec['summary_text'].split('. ') if s.strip()]
    risk_annotation = risk_annotator.analyze_and_underline_summary(sum_sentences)

    result = {
        'record_id': rec['id'],
        'filename': rec['filename'],
        'doc_type': rec['doc_type'],
        'method_used': 'Archived Database Record',
        'algorithm_used': 'Extractive Hybrid Ensemble',
        'original_words': rec['original_words'],
        'summary_words': rec['summary_words'],
        'all_sentence_count': max(1, len(sum_sentences) * 3),
        'summary_sentence_count': len(sum_sentences),
        'accuracy_score': rec['accuracy_score'],
        'compression_ratio': rec['compression_ratio'],
        'time_saved_minutes': max(1, int(round((rec['original_words'] - rec['summary_words']) / 200))),
        'summary_text': rec['summary_text'],
        'summary_sentences': sum_sentences,
        'clauses': rec['clauses'],
        'legalese': rec['legalese'],
        'risk_analysis': {
            'level': rec['risk_level'],
            'score': rec['risk_score'],
            'safety_index': 100 - rec['risk_score'],
            'flags': []
        },
        'readability_summary': {'difficulty': 'Extracted Legal Precision', 'grade_level': 12.0},
        'annotated_sentences': risk_annotation["annotated_sentences"],
        'detected_risk_factors': risk_annotation["detected_risks"],
        'total_summary_risks': risk_annotation["total_risk_count"],
        'summary_underlined_html': risk_annotation["summary_underlined_html"],
        'supported_languages': SUPPORTED_LANGUAGES
    }
    return render_template('result.html', result=result)

@app.route('/api/translate', methods=['POST'])
def api_translate():
    """
    Translates legal summary text or sentences to any selected native language.
    Cached in-memory for instant switching.
    """
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        data = {}

    target_lang = data.get('target_lang', 'en').strip().lower()
    source_lang = data.get('source_lang', 'en').strip().lower()
    sentences = data.get('sentences', [])
    text = data.get('text', '')

    lang_meta = translator.get_lang_meta(target_lang)

    if sentences and isinstance(sentences, list):
        translated_sentences = translator.translate_sentences(sentences, target_lang=target_lang, source_lang=source_lang)
        translated_text = " ".join([s for s in translated_sentences if s])
    elif text:
        translated_text = translator.translate_text(text, target_lang=target_lang, source_lang=source_lang)
        translated_sentences = [s.strip() for s in translated_text.split('. ') if s.strip()]
    else:
        translated_text = ""
        translated_sentences = []

    return jsonify({
        "success": True,
        "target_lang": target_lang,
        "lang_name": lang_meta["name"],
        "native_name": lang_meta["native"],
        "flag": lang_meta["flag"],
        "translated_text": translated_text,
        "translated_sentences": translated_sentences
    })

@app.route('/download-pdf/<int:summary_id>')
@login_required
def download_summary_pdf(summary_id):
    """Generates and streams an official PDF summary brief."""
    rec = get_summary_by_id(summary_id)
    if not rec:
        abort(404)

    summary_data = {
        'filename': rec['filename'],
        'original_words': rec['original_words'],
        'summary_words': rec['summary_words'],
        'accuracy_score': rec['accuracy_score'],
        'compression_ratio': rec['compression_ratio'],
        'summary_text': rec['summary_text'],
        'summary_sentences': [s.strip() for s in rec['summary_text'].split('. ') if s.strip()],
        'clauses': rec['clauses'],
        'legalese': rec['legalese'],
        'risk_analysis': {'level': rec['risk_level'], 'score': rec['risk_score']}
    }

    base_name = os.path.splitext(rec['filename'])[0]
    pdf_path = report_gen.generate_pdf(base_name, rec['filename'], summary_data)
    
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"Official_Legal_Summary_{base_name}.pdf",
        mimetype='application/pdf'
    )

@app.route('/history')
@login_required
def history():
    """Lists audit trail of processed legal instruments."""
    user_id = session.get('user_id')
    summaries = get_user_summaries(user_id)
    return render_template('history.html', summaries=summaries)

@app.route('/delete-summary/<int:summary_id>', methods=['POST'])
@login_required
def delete_summary_route(summary_id):
    user_id = session.get('user_id')
    delete_summary(summary_id, user_id=user_id)
    flash("Record successfully expunged from history ledger.", "info")
    return redirect(url_for('history'))

@app.route('/compare', methods=['GET', 'POST'])
@login_required
def compare_documents():
    """Unique feature: Compare two contract versions (Redline & Extractive Clause Diff)."""
    comparison_result = None
    if request.method == 'POST':
        doc1_text = request.form.get('doc1_text', '').strip()
        doc2_text = request.form.get('doc2_text', '').strip()

        if not doc1_text or not doc2_text:
            flash("Please supply content for both legal instruments to execute comparative audit.", "warning")
            return render_template('compare.html', comparison=None)

        # Run summaries for both
        sum1 = summarizer_engine.summarize(doc1_text, ratio=0.25)
        sum2 = summarizer_engine.summarize(doc2_text, ratio=0.25)

        # Compare clauses
        clauses1_keys = set(sum1['clauses'].keys())
        clauses2_keys = set(sum2['clauses'].keys())
        
        shared_clauses = list(clauses1_keys.intersection(clauses2_keys))
        only_in_1 = list(clauses1_keys - clauses2_keys)
        only_in_2 = list(clauses2_keys - clauses1_keys)

        comparison_result = {
            'doc1': sum1,
            'doc2': sum2,
            'shared_clauses': shared_clauses,
            'only_in_1': only_in_1,
            'only_in_2': only_in_2,
            'risk_delta': sum2['risk_analysis']['score'] - sum1['risk_analysis']['score']
        }

    return render_template('compare.html', comparison=comparison_result)

@app.route('/glossary')
def glossary():
    """Searchable repository of legal jargon and statutory expressions."""
    from summarizer.legal_knowledge import LEGAL_GLOSSARY
    return render_template('glossary.html', glossary=LEGAL_GLOSSARY)

@app.route('/about')
def about():
    """System architecture and research methodology guide."""
    return render_template('about.html')

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
