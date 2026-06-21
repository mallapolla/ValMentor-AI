// AI Career Mentor Chat Handler
function initChatWorkspace() {
    const chatContainer = document.getElementById("chat-messages-container");
    const chatForm = document.getElementById("chat-query-form");
    const chatInput = document.getElementById("chat-query-input");

    // Auto scroll bottom
    const scrollToBottom = () => {
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    };

    // Scroll bottom on boot
    scrollToBottom();

    // Trigger typing indicator when posting
    if (chatForm) {
        chatForm.addEventListener("submit", () => {
            const typingIndicator = document.getElementById("chat-typing-indicator");
            if (typingIndicator) {
                typingIndicator.classList.remove("hidden");
            }
            scrollToBottom();
            
            // Clear input field slowly
            setTimeout(() => {
                if (chatInput) chatInput.value = "";
            }, 10);
        });
    }

    // Scroll bottom on HTMX swap
    document.body.addEventListener("htmx:afterSwap", (evt) => {
        const typingIndicator = document.getElementById("chat-typing-indicator");
        if (typingIndicator) {
            typingIndicator.classList.add("hidden");
        }
        scrollToBottom();
    });
}

document.addEventListener("DOMContentLoaded", initChatWorkspace);
