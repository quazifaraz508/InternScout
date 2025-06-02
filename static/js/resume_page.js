document.addEventListener("DOMContentLoaded", function () {
    const fileInput = document.getElementById("fileInput");
    const dropArea = document.getElementById("dropArea");
    const analysisSection = document.getElementById("analysisSection");
    const uploadBtn = document.getElementById("uploadBtn");
    const darkModeToggle = document.getElementById("darkModeToggle");
    const scoreDisplay = document.getElementById("score");
    const recommendationsList = document.getElementById("recommendations");

    // ✅ Load Dark Mode Preference
    if (localStorage.getItem("theme") === "dark") {
        document.documentElement.setAttribute("data-theme", "dark");
        darkModeToggle.textContent = "☀️ Light Mode";
    }

    // ✅ Open File Picker on Button Click
    uploadBtn.addEventListener("click", () => fileInput.click());

    // ✅ Drag & Drop Events
    dropArea.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropArea.classList.add("border-purple-500", "bg-purple-50", "dark:bg-gray-700");
    });

    dropArea.addEventListener("dragleave", () => {
        dropArea.classList.remove("border-purple-500", "bg-purple-50", "dark:bg-gray-700");
    });

    dropArea.addEventListener("drop", (e) => {
        e.preventDefault();
        dropArea.classList.remove("border-purple-500", "bg-purple-50", "dark:bg-gray-700");

        const file = e.dataTransfer.files[0];
        handleFileUpload(file);
    });

    // ✅ Handle File Selection
    fileInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        handleFileUpload(file);
    });

    function handleFileUpload(file) {
        if (!file) return;

        const validTypes = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"];
        if (!validTypes.includes(file.type)) {
            alert("❌ Invalid file type. Please upload a PDF or DOCX file.");
            return;
        }

        // ✅ Prepare Form Data
        let formData = new FormData();
        formData.append("resume", file);

        // ✅ Send AJAX Request to Django
        fetch("/upload_resume/", {
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": getCSRFToken(),
            },
        })
            .then(response => response.json())
            .then(data => {
                if (!data || data.error) {
                    alert(`❌ Error: ${data?.error || "Unknown error occurred"}`);
                    return;
                }

                // ✅ Display Analysis Results
                analysisSection.classList.remove("hidden");

                // ✅ Ensure score exists
                if (data.similarity_score !== undefined) {
                    scoreDisplay.textContent = `${data.similarity_score}%`;
                } else {
                    scoreDisplay.textContent = "N/A";
                }

                // ✅ Display Recommendations
                recommendationsList.innerHTML = `
                    <li>Improve alignment with job requirements</li>
                    <li>Highlight technical skills more effectively</li>
                    <li>Ensure ATS compatibility for better visibility</li>
                `;
            })
            .catch(error => {
                console.error("Error:", error);
                alert("❌ Something went wrong! Please try again.");
            });
    }

    // ✅ Dark Mode Toggle
    darkModeToggle.addEventListener("click", () => {
        const isDark = document.documentElement.getAttribute("data-theme") === "dark";
        document.documentElement.setAttribute("data-theme", isDark ? "light" : "dark");
        localStorage.setItem("theme", isDark ? "light" : "dark");
        darkModeToggle.textContent = isDark ? "🌙 Dark Mode" : "☀️ Light Mode";
    });

    // ✅ Function to Get CSRF Token
    function getCSRFToken() {
        let cookieValue = null;
        const cookies = document.cookie.split("; ");
        for (let i = 0; i < cookies.length; i++) {
            const [name, value] = cookies[i].split("=");
            if (name === "csrftoken") {
                cookieValue = decodeURIComponent(value);
                break;
            }
        }
        return cookieValue;
    }
});
