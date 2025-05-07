const config = {
    apiUrl: 'http://localhost:8080/api',
    endpoints: {
        chat: '/nlp/interpret',
        health: '/health'
    },
    maxRetries: 3,
    retryDelay: 1000, // ms
    messageTimeout: 30000, // ms
};

export default config; 