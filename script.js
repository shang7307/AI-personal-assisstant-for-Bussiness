const navItems = document.querySelectorAll(".nav-item");
const viewPanels = document.querySelectorAll(".view-panel");
const themeSwitch = document.getElementById("theme-switch");
const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const emailForm = document.getElementById("email-form");
const emailOutput = document.getElementById("email-output");
const productForm = document.getElementById("product-form");
const productOutput = document.getElementById("product-output");
const typingTemplate = document.getElementById("typing-template");

const chatHistory = [];
const savedTheme = localStorage.getItem("business-assistant-theme");

if (savedTheme === "dark") {
    document.body.classList.add("dark-mode");
    themeSwitch.checked = true;
}

navItems.forEach((item) => {
    item.addEventListener("click", () => {
        navItems.forEach((button) => button.classList.remove("active"));
        viewPanels.forEach((panel) => panel.classList.remove("active"));

        item.classList.add("active");
        document.getElementById(item.dataset.view).classList.add("active");
    });
});

themeSwitch.addEventListener("change", () => {
    document.body.classList.toggle("dark-mode", themeSwitch.checked);
    localStorage.setItem("business-assistant-theme", themeSwitch.checked ? "dark" : "light");
});

function addMessage(role, content) {
    const message = document.createElement("div");
    message.className = `message ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.textContent = content;

    message.appendChild(bubble);
    chatMessages.appendChild(message);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return bubble;
}

function showTypingIndicator() {
    const typingNode = typingTemplate.content.firstElementChild.cloneNode(true);
    chatMessages.appendChild(typingNode);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return typingNode;
}

function typeText(element, text, speed = 18) {
    return new Promise((resolve) => {
        element.textContent = "";
        let index = 0;

        function writeNextCharacter() {
            if (index < text.length) {
                element.textContent += text.charAt(index);
                index += 1;
                chatMessages.scrollTop = chatMessages.scrollHeight;
                setTimeout(writeNextCharacter, speed);
            } else {
                resolve();
            }
        }

        writeNextCharacter();
    });
}

function setOutputState(element, content, isError = false) {
    element.classList.remove("empty-state");
    element.textContent = content;
    element.style.color = isError ? "#d92d20" : "";
}

function setLoadingState(button, isLoading, label) {
    button.disabled = isLoading;
    button.textContent = isLoading ? "Please wait..." : label;
}

async function postJson(url, payload) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "Something went wrong. Please try again.");
    }

    return data;
}

chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = chatInput.value.trim();
    if (!message) {
        addMessage("bot", "Please enter a message before sending.");
        return;
    }

    addMessage("user", message);
    chatHistory.push({ role: "user", content: message });
    chatInput.value = "";

    const typingIndicator = showTypingIndicator();
    const sendButton = chatForm.querySelector("button");
    setLoadingState(sendButton, true, "Send");

    try {
        const data = await postJson("/chat", {
            message,
            history: chatHistory
        });

        typingIndicator.remove();
        const bubble = addMessage("bot", "");
        await typeText(bubble, data.reply);
        chatHistory.push({ role: "assistant", content: data.reply });
    } catch (error) {
        typingIndicator.remove();
        addMessage("bot", error.message);
    } finally {
        setLoadingState(sendButton, false, "Send");
    }
});

emailForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const emailType = document.getElementById("email-type").value;
    const tone = document.getElementById("email-tone").value;
    const prompt = document.getElementById("email-prompt").value.trim();
    const submitButton = emailForm.querySelector("button");

    if (!prompt) {
        setOutputState(emailOutput, "Please describe what the email should say.", true);
        return;
    }

    emailOutput.classList.remove("empty-state");
    emailOutput.style.color = "";
    emailOutput.textContent = "Generating your email...";
    setLoadingState(submitButton, true, "Generate Email");

    try {
        const data = await postJson("/generate-email", {
            email_type: emailType,
            tone,
            prompt
        });
        setOutputState(emailOutput, data.email);
    } catch (error) {
        setOutputState(emailOutput, error.message, true);
    } finally {
        setLoadingState(submitButton, false, "Generate Email");
    }
});

productForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const productName = document.getElementById("product-name").value.trim();
    const features = document.getElementById("product-features").value.trim();
    const submitButton = productForm.querySelector("button");

    if (!productName || !features) {
        setOutputState(productOutput, "Please enter both the product name and features.", true);
        return;
    }

    productOutput.classList.remove("empty-state");
    productOutput.style.color = "";
    productOutput.textContent = "Generating your product description...";
    setLoadingState(submitButton, true, "Generate Description");

    try {
        const data = await postJson("/product-description", {
            product_name: productName,
            features
        });
        setOutputState(productOutput, data.description);
    } catch (error) {
        setOutputState(productOutput, error.message, true);
    } finally {
        setLoadingState(submitButton, false, "Generate Description");
    }
});
