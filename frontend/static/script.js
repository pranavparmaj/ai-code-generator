async function sendPrompt() {

    const prompt = document.getElementById("prompt").value;

    const loading = document.getElementById("loading");

    // Show loading indicator
    loading.style.display = "block";

    const response = await fetch("/generate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ prompt: prompt })
    });

    const data = await response.json();

    // Hide loading indicator
    loading.style.display = "none";

    document.getElementById("html_output").textContent =
        data.generated_html;

    document.getElementById("backend_output").textContent =
        data.backend_code;

    document.getElementById("validation_output").textContent =
        JSON.stringify(data.validation, null, 2);

    const downloadLink = document.getElementById("download_link");

    downloadLink.href = data.download_zip;
    downloadLink.innerText = "Download Generated Project";
}