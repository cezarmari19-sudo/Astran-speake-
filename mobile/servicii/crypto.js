import * as Crypto from 'expo-crypto';

export const generateKeyPair = async () => {
  const privateKeyBytes = await Crypto.getRandomBytesAsync(32);
  const privateKey = Buffer.from(privateKeyBytes).toString('hex');
  const publicKey = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    privateKey
  );
  return { privateKey, publicKey };
};

export const encryptMessage = async (text, recipientPublicKey, myPrivateKey) => {
  const sharedSecret = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    myPrivateKey + recipientPublicKey
  );
  const ivBytes = await Crypto.getRandomBytesAsync(16);
  const iv = Buffer.from(ivBytes).toString('hex');
  const encrypted = xorEncrypt(text, sharedSecret, iv);
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
    // FIX BUG 1: apelăm xorDecrypt, nu xorEncrypt
    return xorDecrypt(encrypted, sharedSecret, iv);
  } catch {
    return '[decriptare eșuată]';
  }
};

const xorEncrypt = (input, key, iv) => {
  const combined = key + iv;
  let result = '';
  for (let i = 0; i < input.length; i++) {
    const charCode = input.charCodeAt(i) ^ combined.charCodeAt(i % combined.length);
    result += String.fromCharCode(charCode);
  }
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