chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {

    if (message.action === "extract_job") {

        saveJob(message.jobData).then(response => {
            sendResponse(response);
        }).catch(error => {
            console.error("Error in saveJob:", error);
            sendResponse({ success: false, error: error.message });
        });

        return true; // Keeps sendResponse active for async operations
    }
});

async function saveJob(jobData) {

    try {
        // ✅ Use Promise-based approach to get user ID
        let userInfo = await getUserInfo();

        if (!userInfo || !userInfo.id) {
            console.error("User id not found");
            return { success: false, error: "User ID not found" };
        }

        // ✅ Now make the API request with the user ID
        let response = await fetch("https://API_LINK/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: jobData, userId: userInfo.id }), // ✅ Send actual user ID
        });

        if (!response.ok) {
            let errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        let result = await response.json();
        console.log("API Response:", result);
        return { success: result.success, error: result.error };

    } catch (error) {
        console.error("Fetch error:", error);
        return { success: false, error: error.message };
    }
}

// ✅ Helper function to get user ID asynchronously
function getUserInfo() {
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
