const conversationList = document.getElementById('conversation-list');
const messagesDiv = document.getElementById('messages');
const userInfoDiv = document.getElementById('user-info');
const convTitle = document.getElementById('conv-title');
const sourceFilter = document.getElementById('source-filter');
const userSearch = document.getElementById('user-search');

let conversations = [];
let filteredConversations = [];
let selectedConvId = null;

async function fetchConversations() {
    let url = 'http://localhost:8080/admin/conversations';
    const params = [];
    if (sourceFilter.value !== 'all') params.push(`source=${sourceFilter.value}`);
    if (userSearch.value) params.push(`user_search=${encodeURIComponent(userSearch.value)}`);
    if (params.length) url += '?' + params.join('&');
    const res = await fetch(url);
    conversations = await res.json();
    filteredConversations = conversations;
    renderConversations();
}

function renderConversations() {
    conversationList.innerHTML = '';
    filteredConversations.forEach(conv => {
        const li = document.createElement('li');
        li.textContent = `[${conv.source}] ${conv.user_name || conv.user_id} - ${conv.last_message}`;
        li.classList.toggle('active', conv.conversation_id === selectedConvId);
        li.onclick = () => selectConversation(conv.conversation_id);
        conversationList.appendChild(li);
    });
}

async function selectConversation(conversation_id) {
    selectedConvId = conversation_id;
    const conv = conversations.find(c => c.conversation_id === conversation_id);
    convTitle.textContent = `Conversación con ${conv.user_name || conv.user_id} (${conv.source})`;
    // Mensajes
    messagesDiv.innerHTML = '<em>Cargando mensajes...</em>';
    const res = await fetch(`http://localhost:8080/admin/conversations/${conversation_id}/messages`);
    const messages = await res.json();
    messagesDiv.innerHTML = '';
    messages.forEach(msg => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `msg ${msg.sender}`;
        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        bubble.textContent = msg.text;
        msgDiv.appendChild(bubble);
        messagesDiv.appendChild(msgDiv);
    });
    // Info usuario
    userInfoDiv.innerHTML = '<em>Cargando usuario...</em>';
    const userRes = await fetch(`http://localhost:8080/admin/users/${conv.user_id}`);
    const user = await userRes.json();
    userInfoDiv.innerHTML = `<b>ID:</b> ${user.id || conv.user_id}<br><b>Nombre:</b> ${user.nombre || '-'}<br><b>Email:</b> ${user.email || '-'}`;
}

sourceFilter.onchange = fetchConversations;
userSearch.oninput = fetchConversations;

// Inicializar
fetchConversations();
