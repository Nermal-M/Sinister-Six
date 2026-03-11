// Railway Complaint System - AI-Powered Chatbot
// Supports multilingual interaction with Google Generative AI

class RailwayChatBot {
  constructor() {
    this.language = localStorage.getItem('language') || 'en';
    this.conversationHistory = [];
    this.userIntent = null;
    this.backendUrl = 'http://127.0.0.1:5000/api/chat';
    this.initializeBot();
  }

  // Initialize chatbot
  initializeBot() {
    this.setupEventListeners();
  }

  // Setup event listeners
  setupEventListeners() {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
      chatInput.addEventListener('keypress', (e) => this.handleInput(e));
    }
  }

  // Handle user input
  handleInput(event) {
    if (event.key === 'Enter') {
      const input = event.target;
      const message = input.value.trim();
      if (message) {
        this.processUserMessage(message);
        input.value = '';
      }
    }
  }

  // Process user message
  async processUserMessage(userMessage) {
    this.conversationHistory.push({
      type: 'user',
      message: userMessage,
      timestamp: new Date()
    });

    this.displayMessage(userMessage, 'user');
    this.displayTypingIndicator();

    try {
      const botResponse = await this.generateResponse(userMessage);
      this.removeTypingIndicator();

      setTimeout(() => {
        this.displayMessage(botResponse, 'bot');
        this.conversationHistory.push({
          type: 'bot',
          message: botResponse,
          timestamp: new Date()
        });
      }, 300);
    } catch (error) {
      this.removeTypingIndicator();
      this.displayMessage('Sorry, I encountered an error. Please try again.', 'bot');
      console.error('Chatbot error:', error);
    }
  }

  // Display typing indicator
  displayTypingIndicator() {
    const messagesContainer = document.getElementById('chatbotMessages');
    if (!messagesContainer) return;

    const typingDiv = document.createElement('div');
    typingDiv.id = 'typingIndicator';
    typingDiv.className = 'message bot';
    typingDiv.innerHTML = `<div class="message-bubble"><span class="typing-dots">● ● ●</span></div>`;
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  // Remove typing indicator
  removeTypingIndicator() {
    const typingDiv = document.getElementById('typingIndicator');
    if (typingDiv) {
      typingDiv.remove();
    }
  }

  // Generate response using backend API
  async generateResponse(userMessage) {
    try {
      const botResponse = await this.getBackendResponse(userMessage);
      return botResponse;
    } catch (error) {
      console.error('Backend Error:', error);
      return this.getFallbackResponse();
    }
  }

  // Get response from backend
  async getBackendResponse(userMessage) {
    try {
      const response = await fetch(this.backendUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          language: this.language,
          history: this.conversationHistory.slice(-5) // Send last 5 messages for context
        })
      });

      if (!response.ok) {
        throw new Error(`Backend Error: ${response.statusText}`);
      }

      const data = await response.json();
      return data.response || this.getFallbackResponse();
    } catch (error) {
      console.error('Error calling backend API:', error);
      return this.getFallbackResponse();
    }
  }

  // Fallback response if AI fails
  getFallbackResponse() {
    const responses = {
      en: "I apologize for the temporary issue. Please try again or visit the main menu for assistance.",
      ta: "தற்காலிக சிக்கலுக்கு மன்னிக்கவும். மீண்டும் முயலவும் அல்லது உதவிக்கு முக்கிய மெனுவைப் பார்க்கவும்.",
      hi: "अस्थायी समस्या के लिए खेद है। कृपया पुनः प्रयास करें या सहायता के लिए मुख्य मेनू देखें।"
    };
    return responses[this.language] || responses['en'];
  }

  // Display message in chatbot UI
  displayMessage(message, sender) {
    const messagesContainer = document.getElementById('chatbotMessages');
    if (!messagesContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    messageDiv.innerHTML = `<div class="message-bubble">${this.escapeHtml(message)}</div>`;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  // Escape HTML to prevent XSS
  escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
  }

  // Update language
  updateLanguage(lang) {
    this.language = lang;
  }

  // Get conversation history
  getHistory() {
    return this.conversationHistory;
  }

  // Clear conversation
  clearConversation() {
    this.conversationHistory = [];
    const messagesContainer = document.getElementById('chatbotMessages');
    if (messagesContainer) {
      messagesContainer.innerHTML = '';
    }
  }
}

// Initialize chatbot globally
let railwayChatBot = null;

document.addEventListener('DOMContentLoaded', () => {
  railwayChatBot = new RailwayChatBot();
});

// Helper function to send message from external code
function sendChatbotMessage(message) {
  if (railwayChatBot) {
    railwayChatBot.processUserMessage(message);
  }
}

// Helper function to update chatbot language
function updateChatbotLanguage(lang) {
  if (railwayChatBot) {
    railwayChatBot.updateLanguage(lang);
  }
}
