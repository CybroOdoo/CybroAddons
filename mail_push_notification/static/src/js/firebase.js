/** @odoo-module **/
import { rpc } from "@web/core/network/rpc";

// Initialize variables
let vapid = '';
let firebaseConfig = {};
let messaging = null;
let push_notification = false;

// Fetch push notification settings for the current company
rpc("/firebase_credentials", {}).then(function (data) {
    if (data && data.push_notification) {
        push_notification = true;
        if ("serviceWorker" in navigator) {
            navigator.serviceWorker.register("/firebase-messaging-sw.js").then(function () {
            }).catch(function (err) {
                console.error('Failed to register service worker:', err);
            });
        }
    }
});
// Fetch Firebase configuration details
rpc("/firebase_config_details", {}).then(function (data) {
    if (data) {
        const json = JSON.parse(data);
        vapid = json.vapid;
        firebaseConfig = json.config;
        // Initialize Firebase app with the retrieved configuration
        firebase.initializeApp(firebaseConfig);
        messaging = firebase.messaging();
        // Function to request notification permission and retrieve token
        function requestPermissionAndRetrieveToken() {
            Notification.requestPermission().then((permission) => {
                if (permission === 'granted') {
                    // Retrieve registration token
                    messaging.getToken({ vapidKey: vapid }).then((currentToken) => {
                        if (currentToken) {
                            // Send the token to the server for subscription
                            rpc("/push_notification", { name: currentToken }).then(function (response) {
                            }).catch(function (error) {
                                console.error('Failed to send token to server:', error);
                            });
                        } else {
                            console.warn('No registration token available');
                        }
                    }).catch((err) => {
                        console.error('Error retrieving token:', err);
                    });
                } else {
                    console.warn('Permission for notifications was denied');
                }
            }).catch((err) => {
                console.error('Unable to get permission to notify:', err);
            });
        }
        // Initialize Firebase messaging and handle incoming messages
        messaging.onMessage((payload) => {
            // Show notification to user
            const notificationTitle = payload.notification.title;
            const notificationOptions = {
                body: payload.notification.body,
                icon: payload.notification.icon
            };
            navigator.serviceWorker.getRegistrations().then((registrations) => {
                registrations[0].showNotification(notificationTitle, notificationOptions);
            }).catch((err) => {
                console.error('Error showing notification:', err);
            });
        });
        // Request permission and retrieve token when the DOM content is loaded
        document.addEventListener('DOMContentLoaded', (event) => {
            requestPermissionAndRetrieveToken();
        });
    }
});
