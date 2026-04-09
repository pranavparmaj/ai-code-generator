from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(r"D:\ai_code_generator")
OUTPUT_DIR = ROOT / "output" / "pdf"
OUTPUT_PATH = OUTPUT_DIR / "module_prompt_reference.pdf"


MODULES = [
    {
        "title": "CRUD App",
        "name": "crud",
        "prompts": [
            "Create a CRUD app for products with name, status, price and description fields. Add search, filters, dashboard metrics and role-based access.",
            "Build a CRUD system for customers with name, company, status, email and phone fields. Include list, create, edit, delete and dashboard views.",
            "Generate a resource management app for tasks with title, status, owner, due date and description fields, plus table filters and admin controls.",
        ],
    },
    {
        "title": "Product Catalog",
        "name": "product_catalog",
        "prompts": [
            "Build a product catalog system with name, status, price, category and description fields. Include login, dashboard, search, filters and edit/delete actions.",
            "Create a product management app with name, price, category, status and description fields. Add admin/member roles and a searchable table view.",
            "Generate a product catalog portal with create, list, detail, edit and delete pages for products plus dashboard metrics.",
        ],
    },
    {
        "title": "Inventory Management",
        "name": "inventory_management",
        "prompts": [
            "Create an inventory management system with name, sku, status, quantity and description fields. Add table view, stock dashboard, filters and admin controls.",
            "Build an inventory tracker with item name, sku, quantity, status and notes fields. Include login, dashboard and edit/delete operations.",
            "Generate an inventory operations app with searchable item tables, create/edit flows and role-based access for admins and members.",
        ],
    },
    {
        "title": "Employee Management",
        "name": "employee_management",
        "prompts": [
            "Build an employee management system with name, department, role, status and email fields. Include login, dashboard, search, filters and edit/delete actions.",
            "Create an employee manager app with name, team, title, status and email fields plus admin/member access and a searchable table.",
            "Generate an employee operations portal with list, detail, create, update and delete pages and dashboard summaries.",
        ],
    },
    {
        "title": "Customer Management",
        "name": "customer_management",
        "prompts": [
            "Create a customer management system with name, company, status, email and phone fields. Add search, filters, dashboard and role-based access.",
            "Build a customer portal admin app with name, company, status, contact email and phone fields plus create/edit/delete actions.",
            "Generate a customer operations workspace with a searchable table, customer detail pages and admin-only delete controls.",
        ],
    },
    {
        "title": "Ticket System",
        "name": "ticket_system",
        "prompts": [
            "Create a support ticket system with title, priority, status, assignee and description fields. Add table view, filters, dashboard and role-based access.",
            "Build a ticket tracker with title, status, priority, owner and description fields. Include login, list, detail, edit and delete views.",
            "Generate a helpdesk app with dashboard metrics, searchable ticket table and admin/member roles.",
        ],
    },
    {
        "title": "Task Manager",
        "name": "task_manager",
        "prompts": [
            "Build a task manager with title, status, owner, due date and description fields. Include dashboard, search, filters, create/edit/delete and role-based access.",
            "Create a task tracking system with title, owner, status, due date and notes fields plus searchable list and admin controls.",
            "Generate a task operations app with multi-page CRUD flows, dashboard metrics and member read-only access.",
        ],
    },
    {
        "title": "Login",
        "name": "login",
        "prompts": [
            "Build a login form with username and password for an admin workspace.",
            "Create a secure login module for staff users with username and password fields and a redirect to dashboard.",
            "Generate a sign-in page for an operations portal with username, password and a polished login experience.",
        ],
    },
    {
        "title": "Registration",
        "name": "registration",
        "prompts": [
            "Create a registration module with first name, last name, email, password and company fields.",
            "Build a user registration form with first name, last name, email, password, confirm password and address fields.",
            "Generate an onboarding registration flow for customers with full name, email, password, phone and company fields.",
        ],
    },
    {
        "title": "Dashboard",
        "name": "dashboard",
        "prompts": [
            "Create a dashboard module for operations tracking with summary cards and recent activity.",
            "Build an admin dashboard with KPI cards, recent updates and a clean monitoring layout.",
            "Generate a performance dashboard with headline metrics, activity feed and operational overview.",
        ],
    },
    {
        "title": "Contact",
        "name": "contact",
        "prompts": [
            "Create a contact form with name, email, subject and message fields.",
            "Build a contact desk module with name, email, company, subject and message fields.",
            "Generate a support contact page with customer name, email, topic and message fields.",
        ],
    },
    {
        "title": "Profile",
        "name": "profile",
        "prompts": [
            "Create a profile management form with full name, email, phone and address fields.",
            "Build a user profile page with full name, email, mobile, address and bio fields.",
            "Generate an account profile editor with full name, email, phone, address and website fields.",
        ],
    },
    {
        "title": "Feedback",
        "name": "feedback",
        "prompts": [
            "Build a feedback form with name, email, rating and message fields.",
            "Create a customer feedback module with name, email, score and comments fields.",
            "Generate a product feedback page with user name, email, rating and detailed message fields.",
        ],
    },
]


def build_pdf() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=letter,
        topMargin=0.45 * inch,
        bottomMargin=0.45 * inch,
        leftMargin=0.55 * inch,
        rightMargin=0.55 * inch,
        title="Module Prompt Reference",
        author="Codex",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#12344d"),
        spaceAfter=6,
    )
    intro_style = ParagraphStyle(
        "Intro",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#3b4a5a"),
        spaceAfter=8,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        textColor=colors.HexColor("#0f6c7a"),
        spaceBefore=8,
        spaceAfter=3,
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["BodyText"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=10,
        textColor=colors.HexColor("#526071"),
        spaceAfter=4,
    )
    prompt_style = ParagraphStyle(
        "Prompt",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=10.5,
        leftIndent=10,
        firstLineIndent=-10,
        spaceAfter=3,
        textColor=colors.HexColor("#202938"),
    )

    story = [
        Paragraph("Module Prompt Reference", title_style),
        Paragraph(
            "Repo-based reference for the module and app types currently supported by the generator. Each section includes multiple high-signal prompt examples designed to produce stronger output.",
            intro_style,
        ),
    ]

    for index, module in enumerate(MODULES):
        if index in {7}:
            story.append(PageBreak())
        story.append(Paragraph(module["title"], section_style))
        story.append(Paragraph(f"Internal name: <font name='Helvetica-Bold'>{module['name']}</font>", meta_style))
        for prompt in module["prompts"]:
            story.append(Paragraph(f"&bull; {prompt}", prompt_style))
        story.append(Spacer(1, 4))

    doc.build(story)
    return OUTPUT_PATH


if __name__ == "__main__":
    path = build_pdf()
    print(path)
