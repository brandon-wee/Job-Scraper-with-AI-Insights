document.addEventListener("DOMContentLoaded", function () {
    const extractJobBtn = document.getElementById("extract-job");
    const viewJobsBtn = document.getElementById("view-jobs");
    const loadingSpinner = document.getElementById("loading");
    const addUserBtn = document.getElementById("add-user");
    const statusMessage = document.getElementById("status-message"); // ✅ Get status message element

    // ✅ Modify "View Jobs" button to open the Streamlit app in a new tab
    viewJobsBtn.addEventListener("click", () => {
        setStatusMessage("Launching dashboard...", "info"); // ✅ Update status message
        chrome.identity.getProfileUserInfo(info => {
            if (!info.id) {
                console.error("User id not found");
                setStatusMessage("❌ Failed to launch dashboard. Please turn on sync in chrome://settings/", "error"); // ✅ Update status message
                return;
            }
            const streamlitAppURL = `https://API_LINK/?user_id=${encodeURIComponent(info.id)}`; // ✅ Replace with your actual Streamlit app URL
            setStatusMessage("✅ Dashboard launched successfully!", "success"); // ✅ Update status message
            window.open(streamlitAppURL, "_blank"); // Opens in a new tab
        }
        );
    });

    extractJobBtn.addEventListener("click", () => {
        extractJobBtn.disabled = true;  // Disable button
        loadingSpinner.style.display = "block";  // Show spinner
        setStatusMessage("Extracting job data...", "info"); // ✅ Update status message

        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs.length === 0) {
                console.error("No active tab found");
                setStatusMessage("No active tab found.", "error");
                resetUI();
                return;
            }

            chrome.scripting.executeScript({
                target: { tabId: tabs[0].id },
                func: extractJobDetails
            }, (results) => {
                if (chrome.runtime.lastError) {
                    console.error("Script execution error:", chrome.runtime.lastError.message);
                    setStatusMessage("Failed to execute script.", "error");
                    resetUI();
                    return;
                }

                if (results && results[0] && results[0].result) {
                    sendJobData(results[0].result);
                } else {
                    console.error("No job details found");
                    setStatusMessage("No job details found on this page.", "error");
                    resetUI();
                }
            });
        });
    });

    addUserBtn.addEventListener("click", async () => {
        try {
            setStatusMessage("Adding user credentials...", "info");

            let userInfo = await getUserInfo();
            if (!userInfo || !userInfo.id) {
                console.error("User id not found");
                setStatusMessage("❌ Failed to add user credentials. Please turn on sync in chrome://settings/", "error");
                return;
            }

            const addUserAPI = `http://API_LINK/add_user?user_id`;
            
            let response = await fetch(addUserAPI, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: userInfo.id}),
            });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${await response.text()}`);
            }

            let data = await response.json();
            if (data.success) {
                setStatusMessage("✅ User credentials successfully added!", "success");
            } else {
                setStatusMessage("⚠️ User credentials already exist.", "info");
            }
        } catch (error) {
            console.error("Error adding user credentials:", error);
            setStatusMessage("❌ Failed to add user credentials. Please try again later.", "error");
        }
    });

    // Function to extract job details from the page
    function extractJobDetails() {
        let jobDetailsDiv = document.querySelector(".jobs-search__job-details--wrapper");
        let jobURL = window.location.href;

        return {jobDetailsDiv: jobDetailsDiv ? jobDetailsDiv.innerHTML : null, jobURL: jobURL};
    }

    // Function to send job data to background.js
    function sendJobData(jobData) {
        chrome.runtime.sendMessage({ action: "extract_job", jobData: jobData }, (response) => {
            if (response?.success) {
                console.log("Job data saved successfully!");
                setStatusMessage("✅ Job data extracted successfully!", "success");
            } else {
                console.error("Failed to save job:", response?.error);
                setStatusMessage("❌ Failed to save job data.", "error");
            }
            resetUI();
        });
    }

    // Function to update the status message
    function setStatusMessage(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type}`;
    }

    // Function to reset UI after API call
    function resetUI() {
        extractJobBtn.disabled = false;  // Re-enable button
        loadingSpinner.style.display = "none";  // Hide spinner
    }

    async function getUserInfo() {
        return new Promise((resolve, reject) => {
            chrome.identity.getProfileUserInfo(info => {
                if (chrome.runtime.lastError) {
                    reject(new Error(chrome.runtime.lastError.message));
                } else {
                    resolve(info);
                }
            });
        });
    }
});
