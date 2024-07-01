/** @odoo-module **/
import { jsonrpc } from "@web/core/network/rpc_service";

// Initialize variables
let vapid = '';
let firebaseConfig = {};
let messaging = null;
let push_notification = false;

// Fetch push notification settings for the current company
jsonrpc("/firebase_credentials", {}).then(function(data) {
    if (data && data.push_notification) {
        push_notification = true;
        if ("serviceWorker" in navigator) {
            navigator.serviceWorker.register("/firebase-messaging-sw.js").then(function () {
                console.log('Service worker registered successfully.');
            }).catch(function (err) {
                console.error('Failed to register service worker:', err);
            });
        }
    }
});
// Fetch Firebase configuration details
jsonrpc("/firebase_config_details", {}).then(function(data) {
    if (data) {
        const json = JSON.parse(data);
        vapid = json.vapid;
        firebaseConfig = json.config;
        // Initialize Firebase app with the retrieved configuration
        firebase.initializeApp(firebaseConfig);
        messaging = firebase.messaging();
        // Function to request notification permission and retrieve token
        function requestPermissionAndRetrieveToken() {
        console.log('not',Notification)
            Notification.requestPermission().then((permission) => {
            console.log('permission',permission)
                if (permission === 'granted') {
                    console.log('Permission granted');
                    // Retrieve registration token
                    messaging.getToken({ vapidKey: vapid }).then((currentToken) => {
                        console.log('Current token:', currentToken);
                        if (currentToken) {
                            // Send the token to the server for subscription
                            $.post("/push_notification", { name: currentToken }).done(function(response) {
                                console.log('Token sent to server:', response);
                            }).fail(function(error) {
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
