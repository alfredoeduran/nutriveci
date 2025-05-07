import chatService from '../services/chatService.js';

class Chat {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.messagesContainer = null;
        this.inputForm = null;
        this.isProcessing = false;
        
        this.init();
    }
    
    init() {
        // Crear estructura del chat
        this.container.innerHTML = `
            <div class="chat-container">
                <div class="chat-messages"></div>
                <form class="chat-input-form">
                    <input type="text" placeholder="Escribe tu mensaje..." required>
                    <button type="submit">Enviar</button>
                </form>
                <div class="chat-status"></div>
            </div>
        `;
        
        // Inicializar elementos
        this.messagesContainer = this.container.querySelector('.chat-messages');
        this.inputForm = this.container.querySelector('.chat-input-form');
        this.statusElement = this.container.querySelector('.chat-status');
        
        // Configurar eventos
        this.inputForm.addEventListener('submit', this.handleSubmit.bind(this));
        
        // Verificar estado del servicio
        this.checkServiceStatus();
    }
    
    async checkServiceStatus() {
        try {
            const isHealthy = await chatService.checkHealth();
            if (!isHealthy) {
                this.showStatus('El servicio no está disponible. Por favor, intenta más tarde.', 'error');
            }
        } catch (error) {
            this.showStatus('Error al conectar con el servicio.', 'error');
        }
    }
    
    showStatus(message, type = 'info') {
        this.statusElement.textContent = message;
        this.statusElement.className = `chat-status ${type}`;
        
        if (type !== 'error') {
            setTimeout(() => {
                this.statusElement.textContent = '';
                this.statusElement.className = 'chat-status';
            }, 3000);
        }
    }
    
    addMessage(text, isUser = false) {
        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${isUser ? 'user' : 'bot'}`;
        messageElement.innerHTML = `
            <div class="message-content">
                <p>${text}</p>
            </div>
        `;
        
        this.messagesContainer.appendChild(messageElement);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    async handleSubmit(event) {
        event.preventDefault();
        
        if (this.isProcessing) return;
        
        const input = this.inputForm.querySelector('input');
        const text = input.value.trim();
        
        if (!text) return;
        
        this.isProcessing = true;
        this.showStatus('Enviando mensaje...', 'info');
        
        try {
            // Limpiar input
            input.value = '';
            
            // Mostrar mensaje del usuario
            this.addMessage(text, true);
            
            // Enviar mensaje al servidor
            const response = await chatService.sendMessage(text);
            
            // Mostrar respuesta
            if (response.error) {
                this.showStatus(response.error, 'error');
            } else {
                this.addMessage(response.generated_text);
            }
        } catch (error) {
            this.showStatus('Error al enviar el mensaje. Por favor, intenta de nuevo.', 'error');
            console.error('Error:', error);
        } finally {
            this.isProcessing = false;
        }
    }
    
    setUserId(userId) {
        chatService.setUserId(userId);
    }
}

export default Chat; 