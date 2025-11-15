import { model } from "./mainmodule.js";

const chatInput = document.getElementById("chat-input");
const sendButton = document.getElementById("send-btn");
const chatContainer = document.querySelector(".chatbot-container");
const suggestionsContainer = document.getElementById("suggestions");

// Frieren images for moods
const frierenImages = {
    default: "default.jpg",
    happy: "happy.jpg",
    thoughtful: "thoughtful.jpg",
    teasing: "teasing.jpg",
    sad: "sad.png"
};

const predefinedSuggestions = [
    "Tell me a story",
    "What is your favorite spell?",
    "How are you today?",
    "Do you like magic?",
    "What’s the meaning of life?",
    "Can you recommend a book?",
    "Tell me a fun fact",
    "Do you believe in spirits?",
    "How can I stay calm and focused?"
];

let isTyping = false;

// Show Chat Interface
document.getElementById("ask-d").addEventListener("click", () => {
    document.getElementById("front-display").style.display = "none";
    document.getElementById("chat-container").style.display = "flex";
    displaySuggestions(predefinedSuggestions);
});

// Send button and Enter key
sendButton.addEventListener("click", handleAPI);
chatInput.addEventListener("keyup", e => { if(e.key === "Enter") handleAPI(); });

// Handle user input
async function handleAPI() {
    if (isTyping) return;
    const userText = chatInput.value.trim();
    if (!userText) return;

    addUserMessage(userText);
    chatInput.value = "";
    displaySuggestions(predefinedSuggestions);

    await getAIResponse(userText);
}

// Add user chat bubble
function addUserMessage(text) {
    const bubble = document.createElement("div");
    bubble.classList.add("chat-bubble");
    bubble.innerHTML = `
        <div class="row mb-3">
            <div class="col-md-11 d-flex justify-content-end">
                <div class="chat-body-inner user-input p-3 rounded">${text}</div>
            </div>
            <div class="col-md-1 d-flex justify-content-center align-items-start">
                <img class="mascot-avatar" src="parans.jpg" alt="User">
            </div>
        </div>
    `;
    chatContainer.appendChild(bubble);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Get AI response
async function getAIResponse(message) {
    isTyping = true;
    chatInput.disabled = true;
    sendButton.disabled = true;

    try {
        const result = await model.generateContent(message);
        let response = await result.response.text();

        // Detect mood based on response
        const mood = detectMood(response);

        // Split response into sentences for typing animation
        const sentences = response.split(/(?<=[.!?])\s+/);
        for (const sentence of sentences) {
            if (sentence.trim()) await addAIBubble(sentence, mood);
        }
    } catch (err) {
        await addAIBubble("Oops! Something went wrong.", "default");
        console.error(err);
    }

    chatInput.disabled = false;
    sendButton.disabled = false;
    chatInput.focus();
    isTyping = false;
}

// Add AI chat bubble with typing animation
function addAIBubble(text, mood = "default") {
    return new Promise(resolve => {
        const bubble = document.createElement("div");
        bubble.classList.add("ai-response-wrapper");

        bubble.innerHTML = `
            <div class="row mb-3">
                <div class="col-md-1 d-flex justify-content-center align-items-start">
                    <img class="mascot-avatar" src="${frierenImages[mood]}" alt="Frieren">
                </div>
                <div class="col-md-11 d-flex justify-content-start">
                    <div class="chat-body-inner ai-response p-3 rounded"><p></p></div>
                </div>
            </div>
        `;
        chatContainer.appendChild(bubble);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        const pEl = bubble.querySelector("p");
        let i = 0;
        const speed = 40;

        function typeChar() {
            if (i < text.length) {
                pEl.innerHTML += text[i];
                i++;
                chatContainer.scrollTop = chatContainer.scrollHeight;
                setTimeout(typeChar, speed);
            } else resolve();
        }
        typeChar();
    });
}

// Detect mood from AI response (smarter)
function detectMood(text) {
    const lower = text.toLowerCase();
    if (lower.match(/sad|sorry|pain|lost|unhappy/)) return "sad";
    if (lower.match(/happy|joy|smile|glad|delight/)) return "happy";
    if (lower.match(/think|reflect|ponder|contemplate|thoughtful/)) return "thoughtful";
    if (lower.match(/playful|tease|wink|mischievous|tease/)) return "teasing";
    return "default";
}

// Display clickable suggestions
function displaySuggestions(arr) {
    suggestionsContainer.innerHTML = "";
    shuffleArray(arr).slice(0, 4).forEach(s => {
        const btn = document.createElement("button");
        btn.textContent = s;
        btn.classList.add("btn", "btn-light", "m-2");
        btn.addEventListener("click", () => {
            chatInput.value = s;
            handleAPI();
        });
        suggestionsContainer.appendChild(btn);
    });
}

// Shuffle array
function shuffleArray(arr) {
    for (let i = arr.length-1; i>0; i--){
        const j = Math.floor(Math.random()*(i+1));
        [arr[i], arr[j]]=[arr[j], arr[i]];
    }
    return arr;
}

