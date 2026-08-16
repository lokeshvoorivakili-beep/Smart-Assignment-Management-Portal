import os
import uuid
from werkzeug.utils import secure_filename
from config import Config

def allowed_file(filename: str) -> bool:
    """Checks if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_uploaded_file(file, target_folder: str) -> tuple[str, str]:
    """
    Saves an uploaded file with a secure unique filename.
    Returns tuple of (unique_filename, original_filename).
    """
    os.makedirs(target_folder, exist_ok=True)
    orig_name = secure_filename(file.filename)
    ext = orig_name.rsplit('.', 1)[1].lower() if '.' in orig_name else 'bin'
    unique_name = f"{uuid.uuid4().hex}_{orig_name}"
    save_path = os.path.join(target_folder, unique_name)
    file.save(save_path)
    return unique_name, orig_name

def extract_text_from_file(file_path: str) -> str:
    """
    Extracts text content from various file formats (.txt, .py, .cpp, .java, .docx, .pdf).
    Used by the Smart Similarity Checker.
    """
    if not os.path.exists(file_path):
        return ""

    ext = file_path.rsplit('.', 1)[1].lower() if '.' in file_path else ''

    try:
        if ext in ['txt', 'py', 'java', 'cpp', 'c', 'html', 'css', 'js', 'md', 'csv']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()

        elif ext == 'docx':
            try:
                import docx
                doc = docx.Document(file_path)
                return "\n".join([p.text for p in doc.paragraphs])
            except Exception:
                return ""

        elif ext == 'pdf':
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                return text
            except Exception:
                return ""

    except Exception:
        pass

    return ""
