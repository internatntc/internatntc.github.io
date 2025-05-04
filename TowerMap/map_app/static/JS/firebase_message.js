// firebase_message.js
// Import the functions you need from the SDKs you need
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.3.1/firebase-app.js";
import { getDatabase, ref, get, set, onValue } from "https://www.gstatic.com/firebasejs/11.3.1/firebase-database.js";

// This is already initialized in html

// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
import firebaseConfig from './firebase_config.js';

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const db = getDatabase(app);

// Make sendMessage available globally
window.sendMessage = async function () {
    const selectedTowers = [...document.querySelectorAll('#towerInfo input:checked')].map(cb => cb.value);
    const message = document.getElementById('message').value;

    if (selectedTowers.length === 0 || message.trim() === '') {
        alert('Please select at least one tower and enter a message.');
        return;
    }

    let usersToSend = new Set();
    const loadingModal = document.getElementById("loadingModal");

    try {
        // Show loading modal
        loadingModal.style.display = "flex";
        alert("Firebase Connected! Sending message...");

        // Fetch users linked to each tower
        for (const towerId of selectedTowers) {
            const towerRef = ref(db, `user_cells/${towerId}`);
            try {
                const snapshot = await get(towerRef);
                if (snapshot.exists()) {
                    snapshot.val().forEach(user => usersToSend.add(user));
                }
            } catch (error) {
                console.error(`Error fetching users for Tower ${towerId}:`, error);
            }
        }

        usersToSend = [...usersToSend]; // Convert Set to Array
        if (usersToSend.length === 0) {
            alert("No users found for the selected towers.");
            return;
        }

        // Store the message in Firebase under each user and tower
        for (const towerId of selectedTowers) {
            for (const user of usersToSend) {
                const dbRef = ref(db, `messages/tower_${towerId}/user_${user}`);
                await set(dbRef, {
                    message: message,
                    towerId: towerId,
                    timestamp: Date.now()
                });
            }
        }

        alert(`Message sent successfully to ${usersToSend.length} users!`);
    } catch (error) {
        console.error("Error sending message:", error);
        alert("Failed to send message. Please try again.");
    } finally {
        // Hide loading modal
        loadingModal.style.display = "none";
    }
};


window.addUsersToTowers = async function () {
    const selectedTowers = [...document.querySelectorAll('#towerInfo input:checked')].map(cb => cb.value);
    const phoneNumbers = document.getElementById('phoneNumbers').value.split(',').map(num => num.trim());

    if (selectedTowers.length === 0 || phoneNumbers.length === 0) {
        alert('Please select at least one tower and enter phone numbers.');
        return;
    }

    for (const towerId of selectedTowers) {
        const towerRef = ref(db, `user_cells/${towerId}`);
        try {
            const snapshot = await get(towerRef);
            let users = snapshot.exists() ? snapshot.val() : [];

            // Avoid duplicate numbers
            phoneNumbers.forEach(num => {
                if (!users.includes(num)) users.push(num);
            });

            console.log(`Users to be added to Tower ${towerId}:`, users);  // Debugging line

            await set(towerRef, users);
            console.log(`Added users to Tower ${towerId}:`, users);
        } catch (error) {
            console.error(`Error adding users to Tower ${towerId}:`, error);
        }
    }

    alert('Users added to towers successfully!');
};


// Listen for new messages in Firebase
onValue(ref(db, 'messages/'), (snapshot) => {
    const messages = snapshot.val();
    const sentMessagesDiv = document.getElementById("sentMessages");
    sentMessagesDiv.innerHTML = ""; // Clear previous messages

    let allMessages = [];

    // Loop through each tower and its users
    for (const towerId in messages) {
        if (messages.hasOwnProperty(towerId)) {
            const towerMessages = messages[towerId];

            // Loop through each user in the tower
            for (const userId in towerMessages) {
                if (towerMessages.hasOwnProperty(userId)) {
                    const messageData = towerMessages[userId];

                    allMessages.push({
                        towerId,
                        userId,
                        message: messageData.message,
                        timestamp: messageData.timestamp
                    });
                }
            }
        }
    }

    // Sort messages by timestamp in descending order (latest first)
    allMessages.sort((a, b) => b.timestamp - a.timestamp);

    // Append sorted messages to the list
    allMessages.forEach(msg => {
        const li = document.createElement("li");
        li.textContent = `To Tower ${msg.towerId}, User ${msg.userId}: ${msg.message} (Sent at ${new Date(msg.timestamp).toLocaleString()})`;
        sentMessagesDiv.appendChild(li);
    });
});

// function fetchMessages() {
//     fetch('/view-message/')  // Assumes view_messages returns HTML
//         .then(response => response.text())
//         .then(html => {
//             const parser = new DOMParser();
//             const doc = parser.parseFromString(html, 'text/html');
//             const content = doc.querySelector('.row');
//             document.getElementById('messages-container').innerHTML = content ? content.outerHTML : '';
//         })
//         .catch(error => console.error('Error:', error));
// }

// // Fetch every 5 seconds
// setInterval(fetchMessages, 5000);
// fetchMessages();