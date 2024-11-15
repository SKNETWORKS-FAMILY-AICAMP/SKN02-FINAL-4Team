// chat.js

document.addEventListener("DOMContentLoaded", function() {
    const chatBubble = document.querySelector("#chatBubble");
    const cardsContainer = document.querySelector(".cards");

    chatBubble.addEventListener("click", function() {
        // 2x2 그리드로 정렬되도록 active 클래스 추가
        cardsContainer.classList.add("active");

        // 챗봇 활성화 함수 호출
        activateChatbot();
    });
});

// Function to open the chatbot
function activateChatbot() {
    const chatContainer = document.getElementById("chatSection");
    const chatBubble = document.getElementById("chatBubble");

    if (chatContainer) {
        chatContainer.style.display = "flex"; // 챗봇 표시
        chatBubble.style.display = "none"; // 챗버블 숨기기

        initializeChat();

        if (isAuthenticated === 'True') {
            loadChatList();  // 로그인된 사용자의 경우 채팅 목록 로드
        } else {
            // 비로그인 사용자의 경우 채팅 목록 숨기기 또는 초기화
            const chatListElement = document.querySelector(".chat-list");
            if (chatListElement) {
                chatListElement.innerHTML = '';
            }
        }
    } else {
        console.error("chatSection not found in DOM");
    }
}

// Function to close the chatbot
function closeChat() {
    const chatContainer = document.getElementById("chatSection");
    const chatBubble = document.getElementById("chatBubble");
    const cardsContainer = document.querySelector(".cards");

    if (chatContainer) {
        chatContainer.style.display = "none"; // 챗봇 숨김 처리
        chatBubble.style.display = "block"; // "이거어때" 버튼 다시 표시

        // 2x2 그리드 해제
        if (cardsContainer) {
            cardsContainer.classList.remove("active");
        }
    }
}

// Function to retrieve the CSRF token for secure requests
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Function to initialize the chat with the Enter key event listener
function initializeChat() {
    const inputField = document.getElementById("user-input");

    // Remove any existing event listeners first to prevent duplicates
    inputField.removeEventListener("keydown", handleKeyDown);

    function handleKeyDown(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }
    }

    inputField.addEventListener("keydown", handleKeyDown);
}

let currentChatId = null;  // Global variable to store the active chat_id

// Function to send a message
function sendMessage() {
    const userInputElement = document.getElementById("user-input");
    const userInput = userInputElement.value.trim();

    if (userInput === "") {
        return;
    }

    userInputElement.value = "";

    const chatOutput = document.getElementById("chat-output");

    const userMessageRow = document.createElement("div");
    userMessageRow.className = "message-row";

    const userMessage = document.createElement("div");
    userMessage.className = "user-message";
    userMessage.innerText = "You: " + userInput;

    userMessageRow.appendChild(userMessage);
    chatOutput.appendChild(userMessageRow);
    // 스크롤을 맨 아래로 이동
    chatOutput.scrollTop = chatOutput.scrollHeight;

    // Construct the payload
    let payload = {
        message: userInput
    };

    if (isAuthenticated === 'True' && currentChatId !== null) {
        payload.chat_id = currentChatId;
    }

    fetch("/chatbot/get-response/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        const botMessage = document.createElement("p");
        botMessage.className = "bot-message";
        botMessage.innerText = "Bot: " + data.response;

        // 스크롤을 맨 아래로 이동
        chatOutput.appendChild(botMessage);
        chatOutput.scrollTop = chatOutput.scrollHeight;

        if (isAuthenticated === 'True' && data.chat_id) {
            currentChatId = data.chat_id;  // Update chat_id only if a new one is created
            loadChatList();  // Refresh chat list after each user message
        }

        // 제품 데이터가 있으면 카드 업데이트
        if (data.products) {
            updateProductCards(data.products);
        }
    })
    .catch(error => console.error("Error:", error));
}

// Function to update the product cards
function updateProductCards(products) {
    const productSection = document.getElementById("productSection");

    // 제품 섹션 초기화
    productSection.innerHTML = '';

    // 최대 4개의 제품만 표시
    products.slice(0, 4).forEach(item => {
        const card = document.createElement("div");
        card.className = "card";

        if (item.images) {
            const img = document.createElement("img");
            img.src = item.images;
            img.alt = item.title;
            img.style.width = "250px";
            img.style.height = "auto";
            card.appendChild(img);
        } else {
            const p = document.createElement("p");
            p.innerText = "No image available";
            card.appendChild(p);
        }

        const span = document.createElement("span");
        span.className = "card-title";
        span.innerText = item.summarized_title || item.title;
        card.appendChild(span);

        productSection.appendChild(card);
    });
}

function newChat() {
    // Clear the chat output to start a fresh chat session
    const chatOutput = document.getElementById("chat-output");
    chatOutput.innerHTML = ""; // Clear previous messages

    const botPlaceholder = document.createElement("div");
    botPlaceholder.className = "message bot-message";
    botPlaceholder.innerText = "안녕하세요! 무엇을 도와드릴까요?";
    chatOutput.appendChild(botPlaceholder);

    if (isAuthenticated === 'True') {
        // Call Django view to create a new chat session
        fetch("/chatbot/new/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
        })
        .then(response => response.json())
        .then(data => {
            currentChatId = data.chat_id;  // Store the new chat_id
            console.log("New chat session started:", currentChatId);
            // Update chat list dynamically after creating a new chat
            loadChatList();
        })
        .catch(error => console.error("Error creating new chat session:", error));
    } else {
        // 비로그인 사용자의 경우 새로운 채팅 세션을 생성하지 않음
        currentChatId = null;
    }
}

// Function to update the chat list dynamically
function loadChatList() {
    if (isAuthenticated === 'True') {
        fetch("/chatbot/past-chats/")
            .then(response => response.text())
            .then(html => {
                // Replace chat list HTML with the updated list from the server
                document.querySelector(".chat-list").innerHTML = html;
            })
            .catch(error => console.error("Error updating chat list:", error));
    } else {
        // 비로그인 사용자의 경우 채팅 목록 숨기기 또는 초기화
        const chatListElement = document.querySelector(".chat-list");
        if (chatListElement) {
            chatListElement.innerHTML = '';
        }
    }
}

function showChatList() {
    if (isAuthenticated !== 'True') {
        // 비로그인 사용자의 경우 이 기능을 제공하지 않음
        return;
    }
    const chatDetailContainer = document.getElementById("chat-detail-container");
    const chatOutput = document.getElementById("chat-output"); // Main chat output section

    if (chatDetailContainer && chatOutput) {
        chatDetailContainer.style.display = "none"; // Hide the chat detail
        chatOutput.style.display = "block"; // Show the main chat output
    }
}

function loadChatDetail(chatId) {
    if (isAuthenticated !== 'True') {
        // 비로그인 사용자의 경우 이 기능을 제공하지 않음
        return;
    }

    const chatDetailContainer = document.getElementById("chat-detail-container");
    const chatOutput = document.getElementById("chat-output");

    if (chatDetailContainer && chatOutput) {
        chatOutput.style.display = "none"; // Hide the main chat output
        chatDetailContainer.style.display = "block"; // Show the chat detail
    }
    fetch(`/chatbot/chat/${chatId}/`)  // Ensure the URL is correct
        .then(response => response.text())
        .then(data => {
            // Assuming `chat-detail-container` is the div where chat details should be loaded
            if (chatDetailContainer) {
                chatDetailContainer.innerHTML = data;
            } else {
                console.error("Chat detail container not found in DOM");
            }
        })
        .catch(error => console.error("Error loading chat details:", error));
}

// Function to delete a chat and refresh chat history
function deleteChat(chatId) {
    if (isAuthenticated !== 'True') {
        // 비로그인 사용자의 경우 이 기능을 제공하지 않음
        return;
    }

    fetch(`/chatbot/delete-chat/${chatId}/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken")
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log("Chat deleted successfully.");
            loadChatList();  // Refresh chat list after deletion
        } else {
            console.error("Failed to delete chat:", data.message);
        }
    })
    .catch(error => console.error("Error deleting chat:", error));
}

