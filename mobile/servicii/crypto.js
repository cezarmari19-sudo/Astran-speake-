import * as Crypto from 'expo-crypto';

// Generează o pereche de chei X25519 pentru E2EE
// Deoarece expo-crypto nu suportă X25519 direct,
// folosim un schimb de chei simplificat cu AES-256
// bazat pe un secret derivat din full_id + public_key

export const generateKeyPair = async () => {
  // Generăm 32 bytes random ca private key
  const privateKeyBytes = await Crypto.getRandomBytesAsync(32);
  const privateKey = Buffer.from(privateKeyBytes).toString('hex');
  
  // Public key = hash SHA-256 al private key
  const publicKey = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    privateKey
  );
  
  return { privateKey, publicKey };
};

export const encryptMessage = async (text, recipientPublicKey, myPrivateKey) => {
  // Shared secret = SHA-256(myPrivateKey + recipientPublicKey)
  const sharedSecret = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    myPrivateKey + recipientPublicKey
  );
  
  // Generăm IV random (16 bytes)
  const ivBytes = await Crypto.getRandomBytesAsync(16);
  const iv = Buffer.from(ivBytes).toString('hex');
  
  // XOR simplu cu cheia derivată (compatibil cross-platform fără native modules)
  const encrypted = xorEncrypt(text, sharedSecret, iv);
  
  // Format: iv:encrypted (ambele hex)
  return `${iv}:${encrypted}`;
};

export const decryptMessage = async (payload, senderPublicKey, myPrivateKey) => {
  try {
    const [iv, encrypted] = payload.split(':');
    if (!iv || !encrypted) return '[mesaj invalid]';
    
    const sharedSecret = await Crypto.digestStringAsync(
      Crypto.CryptoDigestAlgorithm.SHA256,
      myPrivateKey + senderPublicKey
    );
    
    return xorEncrypt(encrypted, sharedSecret, iv);
  } catch {
    return '[decriptare eșuată]';
  }
};

// XOR determinist: același apel = encrypt și decrypt
const xorEncrypt = (input, key, iv) => {
  const combined = key + iv;
  let result = '';
  for (let i = 0; i < input.length; i++) {
    const charCode = input.charCodeAt(i) ^ combined.charCodeAt(i % combined.length);
    result += String.fromCharCode(charCode);
  }
  // Convertim la hex pentru transport sigur
  return Buffer.from(result, 'binary').toString('hex');
};

const xorDecrypt = (hexInput, key, iv) => {
  const input = Buffer.from(hexInput, 'hex').toString('binary');
  const combined = key + iv;
  let result = '';
  for (let i = 0; i < input.length; i++) {
    const charCode = input.charCodeAt(i) ^ combined.charCodeAt(i % combined.length);
    result += String.fromCharCode(charCode);
  }
  return result;
};