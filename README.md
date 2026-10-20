# AI Code Generator

A local Flask application that turns natural-language prompts into starter Flask projects. It includes prompt parsing, HTML and backend generation, snippet retrieval, generated-project checks, ZIP export, project previews, generation history, and an optional chatbot backed by Gemini or a local Ollama server.

New to Git and Python? Follow the [step-by-step PC setup guide](output/pdf/ai_code_generator_pc_setup_guide.pdf) to install prerequisites, clone the repository, run the app, and optionally configure Gemini or Ollama.

## Requirements

- Python 3.10 or newer
- Git (to clone this repository)
- A Gemini API key only if you want to use Gemini chat
- Ollama and the `phi` model only if you want to use Ollama chat

The core project-generation features do not require either chat provider. Vector-based retrieval is optional; without its optional packages/index, retrieval uses the built-in keyword ranking.

## Get the project

```bash
git clone https://github.com/pranavparmaj/ai-code-generator.git
cd ai-code-generator
```

## Create an isolated Python environment

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks environment activation, open Command Prompt and run:

```bat
py -3 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configure Gemini chat (optional)

Create a Gemini API key in your own Google AI Studio account. Do not paste the key into source code or commit it to Git. Set it in the terminal session that will run the app.

Windows PowerShell:

```powershell
$env:GEMINI_API_KEY = "your-own-key"
```

macOS or Linux:

```bash
export GEMINI_API_KEY="your-own-key"
```

If the variable is not set, project generation remains available, while Gemini chat reports that it needs a key. The key is read by the backend process and is not stored in this repository.

## Configure Ollama chat (optional)

Install and start Ollama separately, then make sure the `phi` model is available. The application calls Ollama at `http://localhost:11434` and currently uses the model name `phi`. Ollama is not installed by `requirements.txt`.

## Run the application

Run the backend from its directory so its local Python modules can be imported:

```bash
cd backend
python app.py
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser. Stop the server with `Ctrl+C`.

The development server binds to `127.0.0.1` and debug mode is off by default. For local development only, set `FLASK_DEBUG=true` before starting it. Do not enable Flask debug mode on a network-accessible or production deployment.

## What the app creates locally

- Generated project folders and ZIP files are written under `generated_projects/`.
- Generation history is stored in `data/generation_history.json`.
- Application logs are written to `data/app.log`.
- Optional vector-search indexes are stored under `vector_db/`.

These are local runtime files and are ignored by Git. The source snippet catalog in `data/snippet_metadata.json` is part of the project and should remain in place.

## Troubleshooting

- **`ModuleNotFoundError` while starting:** activate the virtual environment and run `pip install -r requirements.txt` again. Start the app with the working directory set to `backend`.
- **Gemini chat says a key is required:** set `GEMINI_API_KEY` in the same terminal session before running `python app.py`.
- **Ollama chat cannot connect:** start Ollama and confirm it is listening on `localhost:11434` with the configured `phi` model available.
- **Port 5000 is busy:** set another port before starting. In PowerShell use `$env:FLASK_RUN_PORT = "5001"`; in macOS or Linux use `export FLASK_RUN_PORT=5001`.

## Project layout

- `backend/` — Flask routes and generation, parsing, retrieval, validation, and preview logic
- `frontend/` — browser templates, styles, and JavaScript
- `templates/` and `snippets/` — source templates and reusable code snippets
- `data/snippet_metadata.json` — snippet catalog used during retrieval
- `utils/` — ZIP export and diagram utilities
- `output/pdf/` — project reference PDFs

## Notes for deployment

This repository is set up for local use. A public or production deployment needs a production WSGI server, deployment-specific secret configuration, and a security review of generated-project execution and preview behavior. Do not expose the development server directly to the internet.
