async function analyzeDocument() {

    const text =
        document.getElementById("documentText").value;

    const documentType =
        document.getElementById("documentType").value;

    const response = await fetch("/extract", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            text: text,
            document_type: documentType
        })
    });

    const data = await response.json();

document.getElementById("result").innerText =
    JSON.stringify(data, null, 2);

const confidenceBox =
    document.getElementById("confidenceBox");

if (data.confidence === "High") {

    confidenceBox.innerHTML =
        "<h3 style='color:green;'>High Confidence</h3>";

} else if (data.confidence === "Medium") {

    confidenceBox.innerHTML =
        "<h3 style='color:orange;'>Medium Confidence</h3>";

} else if (data.confidence === "Low") {

    confidenceBox.innerHTML =
        "<h3 style='color:red;'>Low Confidence - Human Review Recommended</h3>";
}
}