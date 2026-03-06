from flask import Flask, render_template, request, jsonify

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

    print("User Prompt:", prompt)

    return jsonify({
        "status": "success",
        "message": "Prompt received",
        "prompt": prompt
    })


if __name__ == "__main__":
    app.run(debug=True)