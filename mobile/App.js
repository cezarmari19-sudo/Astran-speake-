import { useEffect, useState } from 'react';
import { Modal, View, Text, Pressable, Linking, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import AsyncStorage from '@react-native-async-storage/async-storage';
import WelcomeScreen from './ecrane/WelcomeScreen';
import ChatsScreen from './ecrane/ChatsScreen';
import ChatScreen from './ecrane/ChatScreen';

const Stack = createNativeStackNavigator();
const DONATION_KEY = 'last_donation_prompt';
const INTERVAL_MS = 24 * 60 * 60 * 1000;

export default function App() {
  const [showDonation, setShowDonation] = useState(false);

  useEffect(() => {
    const checkDonation = async () => {
      try {
        const last = await AsyncStorage.getItem(DONATION_KEY);
        if (!last || Date.now() - parseInt(last) > INTERVAL_MS) {
          setShowDonation(true);
          await AsyncStorage.setItem(DONATION_KEY, Date.now().toString());
        }
      } catch {}
    };
    checkDonation();
  }, []);

  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Welcome">
        <Stack.Screen name="Welcome" component={WelcomeScreen} options={{ headerShown: false }} />
        <Stack.Screen name="Chats" component={ChatsScreen} options={{ title: 'Astran' }} />
        <Stack.Screen name="Chat" component={ChatScreen} />
      </Stack.Navigator>

      <Modal visible={showDonation} transparent animationType="fade">
        <View style={styles.overlay}>
          <View style={styles.card}>
            <Text style={styles.title}>Susține Astran Chat ☕</Text>
            <Text style={styles.body}>
              Astran Chat e gratuit și fără reclame. Dacă îți place, o donație mică ajută la menținerea serverului.
            </Text>
            <Pressable
              style={styles.btn}
              onPress={() => {
                Linking.openURL('https://buymeacoffee.com/AstranAi');
                setShowDonation(false);
              }}
            >
              <Text style={styles.btnText}>Donează ☕</Text>
            </Pressable>
            <Pressable onPress={() => setShowDonation(false)}>
              <Text style={styles.skip}>Nu acum</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    width: '100%',
    alignItems: 'center',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 12,
    textAlign: 'center',
  },
  body: {
    fontSize: 15,
    color: '#444',
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 22,
  },
  btn: {
    backgroundColor: '#FFDD00',
    paddingVertical: 12,
    paddingHorizontal: 32,
    borderRadius: 24,
    marginBottom: 12,
  },
  btnText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#000',
  },
  skip: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
});