const BASE_URL = 'https://astran-speake.onrender.com';

export const registerUser = async (fullId, publicKey, username) => {
  const res = await fetch(`${BASE_URL}/users/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      full_id: fullId,
      public_key: publicKey,
      username: username,
    }),
  });
  return res.json();
};

export const findUser = async (displayId) => {
  const res = await fetch(`${BASE_URL}/users/${displayId}`);
  return res.json();
};

export const sendMessage = async (senderId, recipientId, payload) => {
  const res = await fetch(`${BASE_URL}/messages/send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sender_id: senderId,
      recipient_id: recipientId,
      encrypted_payload: payload,
      message_type: 'text',
    }),
  });
  return res.json();
};

export const connectWebSocket = (userId, onMessage) => {
  const ws = new WebSocket(
    `wss://astran-speake.onrender.com/ws/${userId}`
  );
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  ws.onerror = (e) => console.error('WS error:', e);
  ws.onclose = () => console.log('WS închis');
  return ws;
};