from flask import Flask, render_template, request, jsonify
from prompt_parser import parse_prompt
from field_extractor import build_field_schema

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():

    data = request.json
    prompt = data.get("prompt")

    parsed_prompt = parse_prompt(prompt)

    fields = parsed_prompt["fields"]

    field_schema = build_field_schema(fields)

    response = {
        "module": parsed_prompt["module"],
        "framework": parsed_prompt["framework"],
        "language": parsed_prompt["language"],
        "fields": field_schema
    }

    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True)