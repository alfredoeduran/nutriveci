const chatWindow = document.getElementById('chat-window');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');

// Función para agregar mensajes al chat
function addMessage(text, sender = 'bot') {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);
    const bubble = document.createElement('div');
    bubble.classList.add('bubble', sender);
    bubble.textContent = text;
    messageDiv.appendChild(bubble);
    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Mensaje de bienvenida
addMessage('¡Hola! Soy NutriVeci, tu asistente nutricional. ¿En qué puedo ayudarte hoy?');

// Generar y almacenar user_id único en localStorage
let user_id = localStorage.getItem('nutriveci_user_id');
if (!user_id) {
    if (window.crypto && window.crypto.randomUUID) {
        user_id = window.crypto.randomUUID();
    } else {
        // Fallback simple si el navegador no soporta randomUUID
        user_id = 'u-' + Math.random().toString(36).substr(2, 16) + Date.now();
    }
    localStorage.setItem('nutriveci_user_id', user_id);
}

// Manejar envío de formulario
chatForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text) return;
    addMessage(text, 'user');
    userInput.value = '';

    // Si el mensaje contiene la palabra 'receta', consultar la API
    if (text.toLowerCase().includes('receta')) {
        addMessage('Buscando recetas...');
        try {
            // Petición a la API de recetas (ajusta la URL si es necesario)
            const response = await fetch('http://localhost:8080/recipes');
            if (!response.ok) throw new Error('No se pudo obtener recetas');
            const recetas = await response.json();
            if (recetas.length === 0) {
                addMessage('No se encontraron recetas disponibles.');
            } else {
                recetas.slice(0, 3).forEach(receta => {
                    addMessage(
                        `🍽️ <b>${receta.name}</b>\n` +
                        (receta.description ? receta.description + '\n' : '') +
                        `⏱️ ${receta.cooking_time || 'N/D'} min | Dificultad: ${receta.difficulty || 'N/D'}\n` +
                        (receta.tags && receta.tags.length > 0 ? 'Etiquetas: ' + receta.tags.join(', ') : ''),
                        'bot'
                    );
                });
                if (recetas.length > 3) {
                    addMessage(`Mostrando 3 de ${recetas.length} recetas. Especifica mejor tu búsqueda para más resultados.`, 'bot');
                }
            }
        } catch (err) {
            addMessage('Ocurrió un error al consultar recetas. Intenta de nuevo.', 'bot');
        }
    } else {
        // Integración real: enviar mensaje a /nlp/interpret
        addMessage('Procesando tu mensaje...');
        try {
            const response = await fetch('http://localhost:8080/nlp/interpret', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text, user_id })
            });
            if (!response.ok) throw new Error('No se pudo procesar tu mensaje');
            const nlp = await response.json();
            addMessage(nlp.generated_text || 'No se obtuvo respuesta del modelo.', 'bot');
        } catch (err) {
            addMessage('Ocurrió un error al consultar el modelo NLP. Intenta de nuevo.', 'bot');
        }
    }
});
