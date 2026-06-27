const BASE_URL = 'https://astran-speake.onrender.com';

// ─── Utilitare ────────────────────────────────────────────────
const parseResponse = async (res) => {
  const raw = await res.text();
  
  // Încearcă JSON; dacă eșuează, înseamnă că serverul a returnat HTML/text
  let data;
  try {
    data = JSON.parse(raw);
  } catch {
    // Render cold-start sau eroare 502/503 care returnează HTML
    throw new Error(
      `Server indisponibil (${res.status}). Te rugăm așteaptă ~30s și încearcă din nou.`
    );
  }

  if (!res.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map(e => e.msg || JSON.stringify(e)).join(', ')
      : typeof detail === 'string'
        ? detail
        : `Eroare HTTP ${res.status}`;
    throw new Error(message);
  }

  return data;
};

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const fetchWithRetry = async (url, options = {}, retries = 3, delayMs = 3000) => {
  let lastError;

  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      const res = await fetch(url, options);
      return await parseResponse(res);
    } catch (err) {
      lastError = err;

      // Erori 4xx (client) → nu are rost să reîncercăm
      const is4xx = err.message?.includes('HTTP 4') || 
                    err.message?.startsWith('Eroare HTTP 4');
      if (is4xx) throw err;

      // Ultima încercare → aruncă eroarea
      if (attempt === retries - 1) break;

      await sleep(delayMs);
    }
  }

  throw lastError;
};

// ─── API Calls ────────────────────────────────────────────────
export const registerUser = async (fullId, publicKey, username) =>
  fetchWithRetry(`${BASE_URL}/users/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      full_id: fullId,
      public_key: publicKey,
      username,
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

export const connectWebSocket = (userId, onMessage, onError, onClose) => {
  const ws = new WebSocket(`wss://astran-speake.onrender.com/ws/${userId}`);
  ws.onmessage = (e) => {
    try {
      onMessage(JSON.parse(e.data));
    } catch {
      console.error('WS: mesaj invalid JSON', e.data);
    }
  };
  ws.onerror = (e) => {
    console.error('WS error:', e);
    onError?.(e);
  };
  ws.onclose = (e) => {
    console.log('WS închis, cod:', e.code);
    onClose?.(e);
  };
  return ws;
};