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

    htmlOutput.textContent = data.generated_html;
    backendOutput.textContent = data.backend_code;
    validationOutput.textContent = JSON.stringify(data.validation, null, 2);
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

async function copyBackend() {
    if (!backendOutput.textContent) {
        return;
    }
    await navigator.clipboard.writeText(backendOutput.textContent);
}

document.getElementById("generate_button").addEventListener("click", sendPrompt);
document.getElementById("copy_backend").addEventListener("click", copyBackend);
document.getElementById("use_sample").addEventListener("click", () => applySample(0));
document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => setTab(tab.dataset.tab));
});

window.applySample = applySample;

loadSamples();
refreshHistory();
