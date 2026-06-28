import React, { useEffect, useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet,
  ActivityIndicator, TextInput, Alert
} from 'react-native';
import { registerUser } from '../servicii/api';
import { saveIdentity, getIdentity } from '../servicii/stocare';
import { generateKeyPair } from '../servicii/crypto';

const generateId = () => {
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
  let id = '';
  for (let i = 0; i < 20; i++) {
    id += chars[Math.floor(Math.random() * chars.length)];
  }
  return id;
};

export default function WelcomeScreen({ navigation }) {
  const [loading, setLoading] = useState(true);
  const [username, setUsername] = useState('');

  useEffect(() => {
    checkIdentity();
  }, []);

  const checkIdentity = async () => {
    try {
      const { fullId } = await getIdentity();
      if (fullId) {
        navigation.replace('Chats');
      } else {
        setLoading(false);
      }
    } catch {
      setLoading(false);
    }
  };

  const createAccount = async () => {
    const trimmed = username.trim();
    if (trimmed.length < 1 || trimmed.length > 10) {
      Alert.alert('Nume invalid', 'Numele trebuie să aibă între 1 și 10 caractere');
      return;
    }
    setLoading(true);
    try {
      const fullId = generateId();
      const { privateKey, publicKey } = await generateKeyPair();

      const result = await registerUser(fullId, publicKey, trimmed);
      if (result?.display_id) {
        await saveIdentity(fullId, result.display_id, trimmed, privateKey, publicKey);
        navigation.replace('Chats');
      } else {
        Alert.alert('Eroare', 'Nu s-a putut crea contul. Încearcă din nou.');
        setLoading(false);
      }
    } catch (e) {
      Alert.alert('Eroare', e.message || 'Probleme de conexiune.');
      setLoading(false);
    }
  };

  if (loading) return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#075E54" />
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Astran</Text>
      <Text style={styles.subtitle}>Mesagerie privată și securizată</Text>
      <TextInput
        style={styles.input}
        placeholder="Alege un nume (max 10 caractere)"
        value={username}
        onChangeText={setUsername}
        maxLength={10}
        autoCapitalize="none"
      />
      <TouchableOpacity style={styles.button} onPress={createAccount}>
        <Text style={styles.buttonText}>Creează cont</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#fff', padding: 24 },
  title: { fontSize: 42, fontWeight: 'bold', color: '#075E54', marginBottom: 10 },
  subtitle: { fontSize: 16, color: '#666', marginBottom: 40 },
  input: { width: '100%', borderWidth: 1, borderColor: '#ddd', borderRadius: 12, padding: 14, fontSize: 16, marginBottom: 16 },
  button: { backgroundColor: '#075E54', padding: 16, borderRadius: 30, width: '100%', alignItems: 'center' },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
});