import React, { useEffect, useState, useRef } from 'react';
import {
  View, Text, FlatList, TextInput,
  TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform
} from 'react-native';
import { sendMessage, connectWebSocket } from '../servicii/api';
import { getIdentity, getMessages, saveMessages } from '../servicii/stocare';

export default function ChatScreen({ route, navigation }) {
  const { contact } = route.params;
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [myId, setMyId] = useState('');
  const wsRef = useRef(null);
  const listRef = useRef(null);

  useEffect(() => {
    navigation.setOptions({ title: contact.username || contact.id });
    init();
    return () => wsRef.current?.close();
  }, []);

  const init = async () => {
    const { fullId } = await getIdentity();
    setMyId(fullId);
    const saved = await getMessages(contact.id);
    setMessages(saved);
    wsRef.current = connectWebSocket(fullId, (msg) => {
      setMessages((prev) => {
        const updated = [...prev, {
          id: Date.now().toString(),
          text: msg.encrypted_payload,
          from: 'them',
        }];
        saveMessages(contact.id, updated);
        return updated;
      });
    });
  };

  const send = async () => {
    if (!text.trim()) return;
    const msg = { id: Date.now().toString(), text: text.trim(), from: 'me' };
    const updated = [...messages, msg];
    setMessages(updated);
    await saveMessages(contact.id, updated);
    await sendMessage(myId, contact.id, text.trim());
    setText('');
    listRef.current?.scrollToEnd();
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={90}
    >
      <FlatList
        ref={listRef}
        data={messages}
        keyExtractor={(item) => item.id}
        onContentSizeChange={() => listRef.current?.scrollToEnd()}
        renderItem={({ item }) => (
          <View style={[styles.bubble, item.from === 'me' ? styles.me : styles.them]}>
            <Text style={styles.bubbleText}>{item.text}</Text>
          </View>
        )}
      />
      <View style={styles.inputBar}>
        <TextInput
          style={styles.input}
          placeholder="Mesaj..."
          value={text}
          onChangeText={setText}
          multiline
        />
        <TouchableOpacity style={styles.sendBtn} onPress={send}>
          <Text style={styles.sendText}>▶</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#ECE5DD' },
  bubble: { maxWidth: '75%', padding: 10, borderRadius: 10, marginVertical: 4, marginHorizontal: 10 },
  me: { backgroundColor: '#DCF8C6', alignSelf: 'flex-end' },
  them: { backgroundColor: '#fff', alignSelf: 'flex-start' },
  bubbleText: { fontSize: 15 },
  inputBar: { flexDirection: 'row', padding: 8, backgroundColor: '#fff', alignItems: 'center' },
  input: { flex: 1, backgroundColor: '#f0f0f0', borderRadius: 20, paddingHorizontal: 14, paddingVertical: 8, fontSize: 15, maxHeight: 100 },
  sendBtn: { backgroundColor: '#075E54', borderRadius: 25, width: 44, height: 44, justifyContent: 'center', alignItems: 'center', marginLeft: 8 },
  sendText: { color: '#fff', fontSize: 18 },
});