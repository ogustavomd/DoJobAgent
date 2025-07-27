// Chat interface functionality for Anna

class AnnaChat {
    constructor() {
        this.messageForm = document.getElementById('messageForm');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.messagesContainer = document.getElementById('messagesContainer');
        this.typingIndicator = document.getElementById('typingIndicator');
        
        this.isLoading = false;
        
        this.initializeEventListeners();
        this.setupTextareaAutoResize();
    }

    initializeEventListeners() {
        // Form submission
        this.messageForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        // Enter key handling (with Shift+Enter for new line)
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Input validation
        this.messageInput.addEventListener('input', () => {
            this.updateSendButtonState();
        });
    }

    setupTextareaAutoResize() {
        this.messageInput.addEventListener('input', () => {
            // Reset height to auto to get the correct scrollHeight
            this.messageInput.style.height = 'auto';
            
            // Set the height to scrollHeight (up to max-height defined in CSS)
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
        });
    }

    updateSendButtonState() {
        const hasText = this.messageInput.value.trim().length > 0;
        this.sendButton.disabled = !hasText || this.isLoading;
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message || this.isLoading) {
            return;
        }

        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.updateSendButtonState();
        
        // Show typing indicator
        this.showTyping();
        
        try {
            this.isLoading = true;
            this.updateSendButtonState();
            
            const response = await this.callAnnaAgent(message);
            
            // Hide typing indicator
            this.hideTyping();
            
            // Add Anna's response
            this.addMessage(response, 'anna');
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTyping();
            this.addErrorMessage('Desculpe, ocorreu um erro. Tente novamente em alguns instantes.');
        } finally {
            this.isLoading = false;
            this.updateSendButtonState();
        }
    }

    async callAnnaAgent(message) {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }

        return data.response;
    }

    addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message-bubble ' + (sender === 'user' ? 'user-message' : 'anna-message');
        
        // Parse content for media URLs
        const parsedContent = this.parseMessageContent(content);
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${parsedContent}
            </div>
            <div class="message-time">
                <small class="text-muted">${this.getCurrentTime()}</small>
            </div>
        `;

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Initialize any feather icons in the new message
        feather.replace();
    }

    parseMessageContent(content) {
        // Convert URLs to clickable links and handle media
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        
        return content.replace(urlRegex, (url) => {
            // Clean URL (remove trailing punctuation)
            const cleanUrl = url.replace(/[.,;:!?]$/, '');
            
            // Check if it's an image URL
            if (this.isImageUrl(cleanUrl)) {
                return `<div class="message-media"><img src="${cleanUrl}" alt="Imagem compartilhada" loading="lazy" onerror="this.style.display='none'" /></div>`;
            }
            // Check if it's a video URL
            else if (this.isVideoUrl(cleanUrl)) {
                return `<div class="message-media"><video src="${cleanUrl}" controls preload="metadata" onerror="this.style.display='none'">Seu navegador não suporta vídeos.</video></div>`;
            }
            // Regular link
            else {
                return `<a href="${cleanUrl}" target="_blank" rel="noopener noreferrer">${cleanUrl}</a>`;
            }
        }).replace(/\n/g, '<br>'); // Convert line breaks to <br>
    }

    isImageUrl(url) {
        return /\.(jpg|jpeg|png|gif|webp|svg)(\?.*)?$/i.test(url) || 
               url.includes('unsplash.com') || 
               url.includes('images.') ||
               url.includes('/image/');
    }

    isVideoUrl(url) {
        return /\.(mp4|webm|ogg|mov|avi)(\?.*)?$/i.test(url) ||
               url.includes('/video/') ||
               url.includes('sample-videos.com');
    }

    addErrorMessage(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <i data-feather="alert-triangle"></i>
            ${message}
        `;
        
        this.messagesContainer.appendChild(errorDiv);
        this.scrollToBottom();
        
        feather.replace();
    }

    showTyping() {
        this.typingIndicator.classList.remove('d-none');
        this.scrollToBottom();
    }

    hideTyping() {
        this.typingIndicator.classList.add('d-none');
    }

    scrollToBottom() {
        setTimeout(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }, 300); // Increased delay to allow for media loading
    }

    getCurrentTime() {
        return new Date().toLocaleTimeString('pt-BR', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
}

// Initialize chat when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AnnaChat();
});

// Service Worker for offline functionality (optional enhancement)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then((registration) => {
                console.log('SW registered: ', registration);
            })
            .catch((registrationError) => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
