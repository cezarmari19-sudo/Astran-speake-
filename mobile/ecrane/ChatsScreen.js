import React, { useEffect, useState } from 'react';
import {
  View, Text, FlatList, TouchableOpacity,
  StyleSheet, TextInput, Alert
} from 'react-native';
import { findUser } from '../servicii/api';
import { getContacts, saveContacts, getIdentity } from '../servicii/stocare';

export default function ChatsScreen({ navigation }) {
  const [contacts, setContacts] = useState([]);
  const [search, setSearch] = useState('');
  const [myUsername, setMyUsername] = useState('');
  const [myDisplayId, setMyDisplayId] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const { displayId, username } = await getIdentity();
    setMyUsername(username);
    setMyDisplayId(displayId);
    const saved = await getContacts();
    setContacts(saved);
  };

  const addContact = async () => {
    if (search.length !== 7) {
      Alert.alert('ID invalid', 'ID-ul trebuie să aibă exact 7 caractere');
      return;
    }
    try {
      const user = await findUser(search);
      if (user?.display_id) {
        const exists = contacts.find(c => c.id === user.display_id);
        if (exists) {
          Alert.alert('Contact existent', 'Acest contact e deja adăugat');
          return;
        }
        const updated = [...contacts, {
          id: user.display_id,
          fullId: user.full_id,       // ← full_id pentru trimitere mesaje
          username: user.username,
          publicKey: user.public_key,  // ← cheia publică pentru criptare
        }];
        await saveContacts(updated);
        setContacts(updated);
        setSearch('');
      } else {
        Alert.alert('User negăsit', 'Niciun utilizator cu acest ID');
      }
    } catch (e) {
      Alert.alert('Eroare', e.message || 'Probleme de conexiune');
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.myName}>{myUsername}</Text>
        <Text style={styles.myId}>ID: {myDisplayId}</Text>
      </View>
      <View style={styles.searchBar}>
        <TextInput
          style={styles.input}
          placeholder="Adaugă contact după ID (7 caractere)"
          value={search}
          onChangeText={setSearch}
          maxLength={7}
          autoCapitalize="none"
        />
        <TouchableOpacity style={styles.addBtn} onPress={addContact}>
          <Text style={styles.addBtnText}>+</Text>
        </TouchableOpacity>
      </View>
      <FlatList
        data={contacts}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.contact}
            onPress={() => navigation.navigate('Chat', { contact: item })}
          >
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>
                {(item.username || item.id)[0].toUpperCase()}
              </Text>
            </View>
            <View>
              <Text style={styles.contactName}>{item.username || item.id}</Text>
              <Text style={styles.contactId}>#{item.id}</Text>
            </View>
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <Text style={styles.empty}>Niciun contact. Adaugă după ID.</Text>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  header: { backgroundColor: '#075E54', padding: 16 },
  myName: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  myId: { color: '#B2DFDB', fontSize: 12, marginTop: 2 },
  searchBar: { flexDirection: 'row', padding: 10, borderBottomWidth: 1, borderColor: '#eee' },
  input: { flex: 1, borderWidth: 1, borderColor: '#ddd', borderRadius: 20, paddingHorizontal: 14, height: 40 },
  addBtn: { backgroundColor: '#075E54', borderRadius: 20, width: 40, height: 40, justifyContent: 'center', alignItems: 'center', marginLeft: 8 },
  addBtnText: { color: '#fff', fontSize: 24, fontWeight: 'bold' },
  contact: { flexDirection: 'row', alignItems: 'center', padding: 16, borderBottomWidth: 1, borderColor: '#f0f0f0' },
  avatar: { width: 48, height: 48, borderRadius: 24, backgroundColor: '#075E54', justifyContent: 'center', alignItems: 'center', marginRight: 14 },
  avatarText: { color: '#fff', fontSize: 20, fontWeight: 'bold' },
  contactName: { fontSize: 16, fontWeight: '500' },
  contactId: { fontSize: 12, color: '#999', marginTop: 2 },
  empty: { textAlign: 'center', marginTop: 40, color: '#999', fontSize: 15 },
});