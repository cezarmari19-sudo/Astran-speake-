import AsyncStorage from '@react-native-async-storage/async-storage';

export const saveIdentity = async (fullId, displayId, username) => {
  await AsyncStorage.setItem('full_id', fullId);
  await AsyncStorage.setItem('display_id', displayId);
  await AsyncStorage.setItem('username', username);
};

export const getIdentity = async () => {
  const fullId = await AsyncStorage.getItem('full_id');
  const displayId = await AsyncStorage.getItem('display_id');
  const username = await AsyncStorage.getItem('username');
  return { fullId, displayId, username };
};

export const saveContacts = async (contacts) => {
  await AsyncStorage.setItem('contacts', JSON.stringify(contacts));
};

export const getContacts = async () => {
  const data = await AsyncStorage.getItem('contacts');
  return data ? JSON.parse(data) : [];
};

export const saveMessages = async (contactId, messages) => {
  await AsyncStorage.setItem(`messages_${contactId}`, JSON.stringify(messages));
};

export const getMessages = async (contactId) => {
  const data = await AsyncStorage.getItem(`messages_${contactId}`);
  return data ? JSON.parse(data) : [];
};