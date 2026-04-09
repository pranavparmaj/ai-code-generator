from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(r"D:\ai_code_generator")
OUTPUT_DIR = ROOT / "output" / "pdf"
OUTPUT_PATH = OUTPUT_DIR / "app_summary_one_page.pdf"


def bullet(text: str) -> str:
    return f'&bull; {text}'


def build_pdf() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=letter,
        topMargin=0.45 * inch,
        bottomMargin=0.45 * inch,
        leftMargin=0.55 * inch,
        rightMargin=0.55 * inch,
        title="AI Code Generator App Summary",
        author="Codex",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=19,
        leading=22,
        textColor=colors.HexColor("#12344d"),
        spaceAfter=8,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=12,
        textColor=colors.HexColor("#0f6c7a"),
        spaceBefore=4,
        spaceAfter=3,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.4,
        leading=10.2,
        textColor=colors.HexColor("#222222"),
        spaceAfter=3,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=body_style,
        leftIndent=8,
        firstLineIndent=-8,
        bulletIndent=0,
        spaceAfter=1.4,
    )
    small_style = ParagraphStyle(
        "Small",
        parent=body_style,
        fontSize=7.8,
        leading=9.3,
        textColor=colors.HexColor("#334155"),
        spaceAfter=2,
    )

    story = [
        Paragraph("AI Code Generator: One-Page App Summary", title_style),
        Paragraph(
            "Repo-based summary generated from the Flask app, frontend template, backend pipeline modules, templates, snippet metadata, and export utilities in this repository.",
            small_style,
        ),
        Paragraph("What It Is", section_style),
        Paragraph(
            "A Flask web app that turns a natural-language prompt into a scaffolded Flask project, returning generated HTML, backend code, validation results, and a downloadable ZIP. The implementation combines rule-based prompt parsing, field-type inference, Jinja template rendering, snippet retrieval, code assembly, validation, and project export.",
            body_style,
        ),
        Paragraph("Who It's For", section_style),
        Paragraph(
            "Primary persona: a developer, student, or internal prototyper who wants to quickly generate simple web app modules such as login, registration, or dashboard flows from a text prompt.",
            body_style,
        ),
        Paragraph("What It Does", section_style),
        Paragraph(bullet("Serves a single-page UI where the user enters a prompt and triggers generation."), bullet_style),
        Paragraph(bullet("Detects module type, framework, language, and requested fields from the prompt."), bullet_style),
        Paragraph(bullet("Infers field input types such as email, password, date, number, tel, textarea, or text."), bullet_style),
        Paragraph(bullet("Renders starter HTML from Jinja templates for supported Flask modules."), bullet_style),
        Paragraph(bullet("Retrieves related Flask code snippets from metadata plus a FAISS vector index."), bullet_style),
        Paragraph(bullet("Assembles backend code, validates Python syntax and basic HTML structure, and reports errors."), bullet_style),
        Paragraph(bullet("Writes a runnable generated project to `generated_projects/` and exports a ZIP download."), bullet_style),
        Paragraph("How It Works", section_style),
        Paragraph(
            "Browser UI (`frontend/templates/index.html` + `frontend/static/script.js`) posts `/generate` to Flask in `backend/app.py`. The request flows through `prompt_parser.py` -> `field_extractor.py` -> `code_generator.py` (Jinja templates in `templates/flask/`) -> `rag_engine.py`, which loads `data/snippet_metadata.json`, generates embeddings with `sentence_transformers`, and queries the FAISS index in `vector_db/snippet_index.faiss` via `vector_store.py`. `code_assembler.py` merges retrieved snippet code, `code_validator.py` checks Python and HTML, `project_generator.py` writes files under `generated_projects/`, and `utils/zip_exporter.py` creates the downloadable archive.",
            body_style,
        ),
        Paragraph("How To Run", section_style),
        Paragraph(bullet("Create or activate a Python environment. Exact setup command: Not found in repo."), bullet_style),
        Paragraph(bullet("Install required packages. Exact dependency file: Not found in repo. Repo evidence shows imports for `flask`, `jinja2`, `sentence_transformers`, `faiss`, and `numpy`."), bullet_style),
        Paragraph(bullet("From `backend/`, run `python app.py`."), bullet_style),
        Paragraph(bullet("Open the local Flask URL shown in the terminal, enter a prompt, and use the generated ZIP link."), bullet_style),
    ]

    doc.build(story)
    return OUTPUT_PATH


if __name__ == "__main__":
    path = build_pdf()
    print(path)
