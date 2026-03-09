async function sendPrompt() {

    const prompt = document.getElementById("prompt").value;

    const response = await fetch("/generate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ prompt: prompt })
    });

    const data = await response.json();

    document.getElementById("response").innerText =
        JSON.stringify(data, null, 2);

    
}