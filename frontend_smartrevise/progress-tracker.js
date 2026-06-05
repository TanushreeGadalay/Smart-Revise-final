// Progress Tracking Helper Functions
// Use these functions to track user progress from any page

const API_BASE = "http://127.0.0.1:5000";

/**
 * Track a completed quiz
 * @param {string} topic - Quiz topic
 * @param {number} score - Score obtained
 * @param {number} total - Total marks
 * @param {array} answers - User answers (optional)
 */
async function trackQuizCompletion(topic, score, total = 10, answers = []) {
    const user = JSON.parse(localStorage.getItem("user"));
    
    if (!user) {
        console.error("User not logged in");
        return false;
    }

    try {
        const response = await fetch(`${API_BASE}/progress/quiz`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: user.email,
                topic: topic,
                score: score,
                total: total,
                date: new Date().toLocaleDateString(),
                answers: answers
            })
        });

        const data = await response.json();

        if (response.ok) {
            console.log("✓ Quiz progress tracked:", data.quiz);
            return true;
        } else {
            console.error("Error tracking quiz:", data.error);
            return false;
        }
    } catch (error) {
        console.error("Error tracking quiz:", error);
        return false;
    }
}

/**
 * Track completed notes reading
 * @param {string} topic - Topic name
 * @param {string} language - Programming language
 */
async function trackNotesCompletion(topic, language = "General") {
    const user = JSON.parse(localStorage.getItem("user"));
    
    if (!user) {
        console.error("User not logged in");
        return false;
    }

    try {
        const response = await fetch(`${API_BASE}/progress/notes`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: user.email,
                topic: topic,
                language: language,
                date: new Date().toLocaleDateString()
            })
        });

        const data = await response.json();

        if (response.ok) {
            console.log("✓ Notes progress tracked:", data.note);
            return true;
        } else {
            console.error("Error tracking notes:", data.error);
            return false;
        }
    } catch (error) {
        console.error("Error tracking notes:", error);
        return false;
    }
}

/**
 * Track logic building problem completion
 * @param {string} problem - Problem name
 * @param {string} language - Programming language
 * @param {string} status - "solved" or "attempted"
 */
async function trackLogicBuildingCompletion(problem, language = "Python", status = "solved") {
    const user = JSON.parse(localStorage.getItem("user"));
    
    if (!user) {
        console.error("User not logged in");
        return false;
    }

    try {
        const response = await fetch(`${API_BASE}/progress/logic-building`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: user.email,
                problem: problem,
                language: language,
                status: status,
                date: new Date().toLocaleDateString()
            })
        });

        const data = await response.json();

        if (response.ok) {
            console.log("✓ Logic building progress tracked:", data.entry);
            return true;
        } else {
            console.error("Error tracking logic building:", data.error);
            return false;
        }
    } catch (error) {
        console.error("Error tracking logic building:", error);
        return false;
    }
}

/**
 * Get current user progress
 */
async function getUserProgress() {
    const user = JSON.parse(localStorage.getItem("user"));
    
    if (!user) {
        console.error("User not logged in");
        return null;
    }

    try {
        const response = await fetch(`${API_BASE}/progress?email=${user.email}`);
        const data = await response.json();

        if (response.ok) {
            return data;
        } else {
            console.error("Error getting progress:", data.error);
            return null;
        }
    } catch (error) {
        console.error("Error getting progress:", error);
        return null;
    }
}

/**
 * Show pop notification for progress tracking
 */
function showProgressNotification(message, type = "success") {
    const notification = document.createElement("div");
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === "success" ? "#4caf50" : "#f44336"};
        color: white;
        border-radius: 5px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 10000;
        font-weight: bold;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;
    
    // Add animation
    const style = document.createElement("style");
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = "slideOut 0.3s ease-out forwards";
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        trackQuizCompletion,
        trackNotesCompletion,
        trackCodingCompletion,
        getUserProgress,
        showProgressNotification
    };
}
