from flask import Flask, render_template, request, jsonify
from prompt_parser import parse_prompt

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

    parsed = parse_prompt(prompt)

    print("Parsed Prompt:", parsed)

    return jsonify(parsed)


if __name__ == "__main__":
    app.run(debug=True)