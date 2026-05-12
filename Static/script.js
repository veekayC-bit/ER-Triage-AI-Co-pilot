async function analyzeDocument() {
    const text = document.getElementById("documentText").value;
    const documentType = document.getElementById("documentType").value;
    const loadingBox = document.getElementById("loadingBox");
    const errorBox = document.getElementById("errorBox");
    const confidenceBox = document.getElementById("confidenceBox");
    const summaryBox = document.getElementById("summaryBox");
    const issuesBox = document.getElementById("issuesBox");
    const recommendationBox = document.getElementById("recommendationBox");

    errorBox.innerHTML = "";
    confidenceBox.innerHTML = "";
    summaryBox.innerHTML = "";
    issuesBox.innerHTML = "";
    recommendationBox.innerHTML = "";

    if (!text.trim()) {
        errorBox.innerHTML = `
            <div class="error-box">
                Please provide document text before analyzing.
            </div>
        `;
        return;
    }

    loadingBox.innerHTML = "<p>Analyzing document...</p>";

    try {
        const response = await fetch("/extract", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                text: text,
                document_type: documentType,
            }),
        });

        const data = await response.json();
        loadingBox.innerHTML = "";

        if (!response.ok || data.error) {
            throw new Error(data.error || "Error processing document.");
        }

        const confidence = (data.confidence || "Low").trim();

        if (confidence === "High") {
            confidenceBox.innerHTML = `
                <div class="success-box">
                    <h3>High Confidence</h3>
                    <p>Extraction completed successfully.</p>
                </div>
            `;
        } else if (confidence === "Medium") {
            confidenceBox.innerHTML = `
                <div class="warning-box">
                    <h3>Medium Confidence</h3>
                    <p>Some fields may require review.</p>
                </div>
            `;
        } else {
            confidenceBox.innerHTML = `
                <div class="error-box">
                    <h3>Low Confidence</h3>
                    <p>Human review recommended.</p>
                </div>
            `;
        }

        let summaryHtml = "<h3>Summary</h3>";

        if (data.summary) {
            for (const key in data.summary) {
                const value = data.summary[key];

                if (Array.isArray(value)) {
                    summaryHtml += `<h4>${escapeHtml(key)}</h4>`;

                    value.forEach(item => {
                        summaryHtml += `
                            <div class="summary-card">
                                ${Object.entries(item)
                                    .map(([k, v]) => `<p><strong>${escapeHtml(k)}:</strong> ${escapeHtml(v)}</p>`)
                                    .join("")}
                            </div>
                        `;
                    });
                } else {
                    summaryHtml += `
                        <p>
                            <strong>${escapeHtml(key)}:</strong>
                            ${escapeHtml(value)}
                        </p>
                    `;
                }
            }
        } else {
            summaryHtml += "<p>No summary returned.</p>";
        }

        summaryBox.innerHTML = summaryHtml;

        let issuesHtml = "<h3>Issues</h3>";

        if (data.issues && data.issues.length > 0) {
            data.issues.forEach(issue => {
                issuesHtml += `
                    <div class="warning-box">
                        ${escapeHtml(issue)}
                    </div>
                `;
            });
        } else {
            issuesHtml += "<p>No issues detected.</p>";
        }

        issuesBox.innerHTML = issuesHtml;

        if (data.recommendation) {
            recommendationBox.innerHTML = `
                <h3>Recommendation</h3>
                <div class="warning-box">
                    ${escapeHtml(data.recommendation)}
                </div>
            `;
        } else {
            recommendationBox.innerHTML = "";
        }
    } catch (error) {
        loadingBox.innerHTML = "";

        errorBox.innerHTML = `
            <div class="error-box">
                ${escapeHtml(error.message)}
            </div>
        `;

        console.error(error);
    }
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
