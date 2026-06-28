import AsyncStorage from '@react-native-async-storage/async-storage';

// ─── Identitate ───────────────────────────────────────────────
export const saveIdentity = async (fullId, displayId, username, privateKey, publicKey) => {
  await AsyncStorage.multiSet([
    ['full_id', fullId],
    ['display_id', displayId],
    ['username', username],
    ['private_key', privateKey],
    ['public_key', publicKey],
  ]);
};

export const getIdentity = async () => {
  const pairs = await AsyncStorage.multiGet([
    'full_id', 'display_id', 'username', 'private_key', 'public_key'
  ]);
  return {
    fullId: pairs[0][1],
    displayId: pairs[1][1],
    username: pairs[2][1],
    privateKey: pairs[3][1],
    publicKey: pairs[4][1],
  };
};

// ─── Contacte ─────────────────────────────────────────────────
export const saveContacts = async (contacts) => {
  await AsyncStorage.setItem('contacts', JSON.stringify(contacts));
};

export const getContacts = async () => {
  const data = await AsyncStorage.getItem('contacts');
  return data ? JSON.parse(data) : [];
};

// ─── Mesaje ───────────────────────────────────────────────────
export const saveMessages = async (contactId, messages) => {
  await AsyncStorage.setItem(`messages_${contactId}`, JSON.stringify(messages));
};

export const getMessages = async (contactId) => {
  const data = await AsyncStorage.getItem(`messages_${contactId}`);
  return data ? JSON.parse(data) : [];
};