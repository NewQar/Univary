const apiBaseUrl = "http://127.0.0.1:5000"; // Flask URL 178 attempt kot.I don't know bruh. Help me
let currentUserToken = null;

//Do not touching. Changing the page function. Case change change from frame to frame uwowowowo go there and there place
function loadPage(pageName) {
    fetch(`${pageName}.html`)
        .then((response) => response.text())
        .then((html) => {
            document.getElementById("app").innerHTML = html; // Replace the content of a container with the HTML
            initializePageScripts(pageName); // Call relevant functions for that page
        })
        .catch((err) => console.error("Error loading page:", err));
}

// Very specific change change frame. Only change variable if change name of frame
function initializePageScripts(pageName) {
    switch (pageName) {
        case "Login":
            setupLoginPage();
            break;
        case "Signup":
            setupSignupPage();
            break;
        case "AwiProfile":
        case "HanProfile":
        case "Profile":
            loadUserProfile();
            break;
        case "University":
            setupUniversityPage();
            break;
        case "Search":
            setupSearchPage();
            break;
        case "WelcomePage":
            setupWelcomePage();
            break;
        default:
            console.log(`No specific scripts for ${pageName}`);
    }
}

// ChatGPT Backend part backup:


function setupLoginPage() {
    const loginForm = document.getElementById("loginForm");
    loginForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const formData = new FormData(loginForm);
        const userData = Object.fromEntries(formData.entries());
        axios
            .post(`${apiBaseUrl}/generate_token`, userData)
            .then((res) => {
                currentUserToken = res.data.token;
                alert("Login successful!");
                loadPage("Main");
            })
            .catch((err) => console.error("Login failed:", err));
    });
}

function setupSignupPage() {
    const signupForm = document.getElementById("signupForm");
    signupForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const formData = new FormData(signupForm);
        const userData = Object.fromEntries(formData.entries());
        // You could add a POST request to your Flask backend for signup logic
        alert("Signup feature not implemented yet!");
    });
}

// ======== AI SECURITY TESTING ========
function setupWelcomePage() {
    document.getElementById("testAI").addEventListener("click", () => {
        axios
            .post(`${apiBaseUrl}/log_activity`, { token: currentUserToken })
            .then((res) => {
                alert(res.data.message);
            })
            .catch((err) => console.error("AI test failed:", err));
    });
}

// ======== MEETING INTEGRATION ========
function connectMeeting(platform) {
    const meetingUrl = document.getElementById("meetingUrl").value;

    axios
        .post(`${apiBaseUrl}/secure_data`, {
            token: currentUserToken,
            meeting_data: { platform, url: meetingUrl },
        })
        .then((res) => {
            if (res.data.message.includes("blocked")) {
                alert("Suspicious activity detected! Connection blocked.");
            } else {
                alert("Meeting connected successfully!");
                window.open(meetingUrl, "_blank");
            }
        })
        .catch((err) => console.error("Meeting connection failed:", err));
}

// ======== PROFILE DATA ========
function loadUserProfile() {
    if (!currentUserToken) {
        alert("You need to log in first!");
        loadPage("Login");
        return;
    }

    axios
        .post(`${apiBaseUrl}/verify_token`, { token: currentUserToken })
        .then((res) => {
            document.getElementById("userProfile").innerHTML = `
                <h2>Welcome, ${res.data.user_id}!</h2>
            `;
        })
        .catch((err) => {
            alert("Session expired. Please log in again.");
            loadPage("Login");
        });
}

// ======== UNIVERSITY PAGE ========
function setupUniversityPage() {
    // Example logic for dynamic university information
    const universityList = [
        { name: "Harvard", info: "A leading university in the USA." },
        { name: "UiTM", info: "A renowned institution in Malaysia." },
    ];

    const uniContainer = document.getElementById("universityInfo");
    universityList.forEach((uni) => {
        const uniDiv = document.createElement("div");
        uniDiv.innerHTML = `
            <h3>${uni.name}</h3>
            <p>${uni.info}</p>
        `;
        uniContainer.appendChild(uniDiv);
    });
}

// ======== SEARCH FUNCTION ========
function setupSearchPage() {
    const searchForm = document.getElementById("searchForm");
    searchForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const query = document.getElementById("searchQuery").value;

        // Dummy search results
        const results = [
            "Result 1: Example description.",
            "Result 2: Another example.",
            "Result 3: More information.",
        ];

        const resultsContainer = document.getElementById("searchResults");
        resultsContainer.innerHTML = "";
        results.forEach((result) => {
            const resultDiv = document.createElement("div");
            resultDiv.textContent = result;
            resultsContainer.appendChild(resultDiv);
        });
    });
}

// ======== PAGE NAVIGATION ========
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-page]").forEach((btn) => {
        btn.addEventListener("click", () => {
            const targetPage = btn.getAttribute("data-page");
            loadPage(targetPage);
        });
    });

    // Default load
    loadPage("WelcomePage");
});

// ======== MEETING CONNECTIONS ========
document.addEventListener("click", (e) => {
    if (e.target.classList.contains("connect-meeting")) {
        const platform = e.target.getAttribute("data-platform");
        connectMeeting(platform);
    }
});
