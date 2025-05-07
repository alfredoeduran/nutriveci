import config from '../config.js';

class ChatService {
    constructor() {
        this.retryCount = 0;
        this.isConnected = false;
        this.userId = null;
    }

    async checkHealth() {
        try {
            const response = await fetch(`${config.apiUrl}${config.endpoints.health}`);
            return response.ok;
        } catch (error) {
            console.error('Error checking health:', error);
            return false;
        }
    }

    setUserId(userId) {
        this.userId = userId;
    }

    async sendMessage(text) {
        if (!this.userId) {
            throw new Error('ID de usuario no configurado');
        }

        if (!this.isConnected) {
            const isHealthy = await this.checkHealth();
            if (!isHealthy) {
                throw new Error('Servicio no disponible');
            }
            this.isConnected = true;
        }

        try {
            const response = await fetch(`${config.apiUrl}${config.endpoints.chat}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text,
                    user_id: this.userId,
                    source: 'web'
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Reset retry count on success
            this.retryCount = 0;
            
            return data;
        } catch (error) {
            console.error('Error sending message:', error);
            
            // Implement retry logic
            if (this.retryCount < config.maxRetries) {
                this.retryCount++;
                await new Promise(resolve => setTimeout(resolve, config.retryDelay * this.retryCount));
                return this.sendMessage(text);
            }
            
            // Reset connection state after max retries
            this.isConnected = false;
            this.retryCount = 0;
            
            throw error;
        }
    }
}

export default new ChatService(); 