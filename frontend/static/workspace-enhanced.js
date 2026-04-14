const sampleList = document.getElementById("sample_list");
const historyList = document.getElementById("history_list");
const loadingCard = document.getElementById("loading");
const progressSteps = document.getElementById("progress_steps");
const errorBanner = document.getElementById("error_banner");
const previewFrame = document.getElementById("preview_frame");
const htmlOutput = document.getElementById("html_output");
const backendOutput = document.getElementById("backend_output");
const validationOutput = document.getElementById("validation_output");
const explanationOutput = document.getElementById("explanation_output");
const snippetList = document.getElementById("snippet_list");
const stageList = document.getElementById("stage_list");
const downloadLink = document.getElementById("download_link");
const projectHeading = document.getElementById("project_heading");
const projectSubheading = document.getElementById("project_subheading");

let cachedSamples = [];
const rawCodeStore = {
    html_output: "",
    backend_output: "",
    validation_output: "",
};

function escapeHtml(value) {
    return (value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

function highlightHtml(code) {
    let escaped = escapeHtml(code);
    escaped = escaped.replace(/(&lt;!--[\s\S]*?--&gt;)/g, '<span class="token-comment">$1</span>');
    escaped = escaped.replace(/(&lt;\/?)([a-zA-Z0-9_-]+)/g, '$1<span class="token-tag">$2</span>');
    escaped = escaped.replace(/([a-zA-Z-:]+)(=)(&quot;.*?&quot;|".*?"|'.*?')/g, '<span class="token-attr-name">$1</span><span class="token-operator">$2</span><span class="token-attr-value">$3</span>');
    escaped = escaped.replace(/(&gt;)/g, '<span class="token-punctuation">$1</span>');
    return escaped;
}

function highlightPython(code) {
    let escaped = escapeHtml(code);
    escaped = escaped.replace(/(#.*)$/gm, '<span class="token-comment">$1</span>');
    escaped = escaped.replace(/("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g, '<span class="token-string">$1</span>');
    escaped = escaped.replace(/\b(from|import|def|return|if|elif|else|for|while|try|except|class|with|as|in|and|or|not|True|False|None)\b/g, '<span class="token-keyword">$1</span>');
    escaped = escaped.replace(/\b([A-Za-z_][A-Za-z0-9_]*)\s*(?=\()/g, '<span class="token-function">$1</span>');
    escaped = escaped.replace(/\b\d+(\.\d+)?\b/g, '<span class="token-number">$&</span>');
    return escaped;
}

function highlightJson(code) {
    let escaped = escapeHtml(code);
    escaped = escaped.replace(/("(?:[^"\\]|\\.)*")(\s*:)/g, '<span class="token-property">$1</span><span class="token-punctuation">$2</span>');
    escaped = escaped.replace(/:\s*("(?:[^"\\]|\\.)*")/g, ': <span class="token-string">$1</span>');
    escaped = escaped.replace(/\b(true|false)\b/g, '<span class="token-boolean">$1</span>');
    escaped = escaped.replace(/\bnull\b/g, '<span class="token-keyword">$&</span>');
    escaped = escaped.replace(/\b-?\d+(\.\d+)?\b/g, '<span class="token-number">$&</span>');
    return escaped;
}

function setHighlightedCode(element, code, language) {
    rawCodeStore[element.id] = code || "";
    if (language === "html") {
        element.innerHTML = highlightHtml(code || "");
        return;
    }
    if (language === "python") {
        element.innerHTML = highlightPython(code || "");
        return;
    }
    if (language === "json") {
        element.innerHTML = highlightJson(code || "");
        return;
    }
    element.textContent = code || "";
}

async function fetchJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Request failed for ${url}`);
    }
    return response.json();
}

function collectOptions() {
    return {
        module: document.getElementById("module").value,
        framework: document.getElementById("framework").value,
        project_name: document.getElementById("project_name").value,
        title: document.getElementById("title").value,
        fields: document.getElementById("fields").value,
        database: document.getElementById("database").value,
        styling: document.getElementById("styling").value,
        notes: document.getElementById("notes").value,
        include_tests: document.getElementById("include_tests").checked,
        include_readme: document.getElementById("include_readme").checked,
        include_sample_data: document.getElementById("include_sample_data").checked,
    };
}

function setLoading(active, steps = []) {
    loadingCard.classList.toggle("hidden", !active);
    progressSteps.innerHTML = steps.map((step) => `<li>${step}</li>`).join("");
}

function setError(message = "") {
    errorBanner.textContent = message;
    errorBanner.classList.toggle("hidden", !message);
}

function updateAnalytics(analytics) {
    document.getElementById("metric_total").textContent = analytics.total_generations || 0;
    document.getElementById("metric_success").textContent = analytics.successful_generations || 0;
    document.getElementById("metric_failed").textContent = analytics.failed_generations || 0;
    document.getElementById("metric_last").textContent = analytics.last_project || "None yet";
    document.getElementById("analytics_badge").textContent = `${analytics.total_generations || 0} runs`;
}

function renderHistory(items) {
    if (!items.length) {
        historyList.innerHTML = "<p>No generation history yet.</p>";
        return;
    }

    historyList.innerHTML = items.map((item) => `
        <article class="history-card">
            <strong>${item.project_name}</strong>
            <p class="history-meta">${item.module} • ${item.framework} • ${item.status}</p>
            <p class="history-meta">${item.created_at || ""}</p>
            ${item.download_url ? `<a href="${item.download_url}" target="_blank">Download saved ZIP</a>` : ""}
        </article>
    `).join("");
}

function renderSamples(samples) {
    cachedSamples = samples;
    sampleList.innerHTML = samples.map((sample, index) => `
        <article class="sample-card">
            <strong>${sample.title}</strong>
            <p>${sample.prompt}</p>
            <button class="secondary-button" type="button" onclick="applySample(${index})">Use prompt</button>
        </article>
    `).join("");
}

function renderGeneration(data) {
    projectHeading.textContent = data.project_name;
    projectSubheading.textContent = `${data.module} module • ${data.framework} • quality score ${data.validation.quality_score}`;

    setHighlightedCode(htmlOutput, data.generated_html, "html");
    setHighlightedCode(backendOutput, data.backend_code, "python");
    setHighlightedCode(validationOutput, JSON.stringify(data.validation, null, 2), "json");
    explanationOutput.textContent = data.explanation;
    previewFrame.srcdoc = data.preview_html;

    snippetList.innerHTML = (data.retrieved_snippets || []).map((snippet) => `<li>${snippet}</li>`).join("") || "<li>No snippets were matched.</li>";
    stageList.innerHTML = (data.steps || []).map((step) => `<li>${step}</li>`).join("");

    downloadLink.href = data.download_url || "#";
    downloadLink.classList.remove("disabled");

    updateAnalytics(data.analytics || {});
}

async function refreshHistory() {
    const data = await fetchJson("/history");
    renderHistory(data.items || []);
    updateAnalytics(data.analytics || {});
}

async function loadSamples() {
    const data = await fetchJson("/samples");
    renderSamples(data.samples || []);
}

async function sendPrompt() {
    setError("");
    setLoading(true, [
        "Parsing request",
        "Building field schema",
        "Rendering template",
        "Retrieving snippets",
        "Assembling backend",
        "Validating project",
        "Exporting zip",
    ]);

    try {
        const response = await fetch("/generate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                prompt: document.getElementById("prompt").value,
                options: collectOptions(),
            }),
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.details || data.error || "Generation failed");
        }

        renderGeneration(data);
        await refreshHistory();
    } catch (error) {
        setError(error.message);
    } finally {
        setLoading(false);
    }
}

function applySample(index) {
    const sample = cachedSamples[index];
    if (!sample) {
        return;
    }
    document.getElementById("prompt").value = sample.prompt;
    document.getElementById("module").value = sample.module;
}

function setTab(tabName) {
    document.querySelectorAll(".tab").forEach((tab) => {
        tab.classList.toggle("active", tab.dataset.tab === tabName);
    });
    document.querySelectorAll(".tab-panel").forEach((panel) => {
        panel.classList.toggle("active", panel.id === `tab-${tabName}`);
    });
}

async function copyCodeById(targetId) {
    if (!rawCodeStore[targetId]) {
        return;
    }
    await navigator.clipboard.writeText(rawCodeStore[targetId]);
}

document.getElementById("generate_button").addEventListener("click", sendPrompt);
document.getElementById("copy_backend").addEventListener("click", () => copyCodeById("backend_output"));
document.getElementById("use_sample").addEventListener("click", () => applySample(0));
document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => setTab(tab.dataset.tab));
});
document.querySelectorAll(".copy-button").forEach((button) => {
    button.addEventListener("click", () => copyCodeById(button.dataset.copyTarget));
});

window.applySample = applySample;

loadSamples();
refreshHistory();




// ================= CHATBOT =================
let chatHistory = [];

function addChatMessage(text, sender) {
    const container = document.getElementById("chat-messages");
    if (!container) return;

    const msg = document.createElement("div");
    msg.classList.add("chat-bubble");

    if (sender === "user") {
        msg.classList.add("user-bubble");
    } else {
        msg.classList.add("bot-bubble");
    }

    msg.innerHTML = text.replace(/\n/g, "<br>");

    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

async function sendChatMessage() {
    console.log("Send button clicked"); // DEBUG

    const input = document.getElementById("chat-input");
    if (!input) {
        console.log("Input not found");
        return;
    }

    const message = input.value.trim();
    console.log("Message:", message);

    if (!message) return;

    addChatMessage(message, "user");
    input.value = "";

    addChatMessage("Thinking...", "bot");

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message,
                context: {
                    backend_code: backendOutput.textContent || "",
                    
                    explanation: explanationOutput.textContent || "",
                    module: document.getElementById("module").value,
                    framework: document.getElementById("framework").value
                }
            })
        });

        const data = await res.json();

        const container = document.getElementById("chat-messages");
        container.removeChild(container.lastChild);

        addChatMessage(data.response || "No response", "bot");

    } catch (err) {
        console.error(err);

        const container = document.getElementById("chat-messages");
        container.removeChild(container.lastChild);

        addChatMessage("Error connecting to chatbot", "bot");
    }
}

function initChatbot() {
    const sendBtn = document.getElementById("chat-send-btn");
    const input = document.getElementById("chat-input");

    if (sendBtn) {
        sendBtn.addEventListener("click", sendChatMessage);
    }

    if (input) {
        input.addEventListener("keypress", function (e) {
            if (e.key === "Enter") {
                sendChatMessage();
            }
        });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    initChatbot();
});

// ---chatbot exit