const BASE_URL = 'https://astran-speake.onrender.com';

const fetchWithRetry = async (url, options = {}, retries = 3, delay = 2000) => {
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(url, options);
      const data = await res.json();
      if (!res.ok) {
        if (res.status >= 400 && res.status < 500) {
          throw new Error(data.detail || `HTTP ${res.status}`);
        }
        throw new Error(`HTTP ${res.status}`);
      }
      return data;
    } catch (err) {
      if (i === retries - 1) throw err;
      if (err.message && err.message.startsWith('HTTP 4')) throw err;
      await new Promise(r => setTimeout(r, delay));
    }
  }
};

export const registerUser = async (fullId, publicKey, username) =>
  fetchWithRetry(`${BASE_URL}/users/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      full_id: fullId,
      public_key: publicKey,
      username: username,
    }),
  });

export const findUser = async (displayId) =>
  fetchWithRetry(`${BASE_URL}/users/${displayId}`);

export const sendMessage = async (senderId, recipientId, payload) =>
  fetchWithRetry(`${BASE_URL}/messages/send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sender_id: senderId,
      recipient_id: recipientId,
      encrypted_payload: payload,
      message_type: 'text',
    }),
  });

export const connectWebSocket = (userId, onMessage) => {
  const ws = new WebSocket(
    `wss://astran-speake.onrender.com/ws/${userId}`
  );
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  ws.onerror = (e) => console.error('WS error:', e);
  ws.onclose = () => console.log('WS închis');
  return ws;
};