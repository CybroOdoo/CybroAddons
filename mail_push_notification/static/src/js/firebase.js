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
                console.warn('Failed to register service worker:', err);
            });
        }
    }
}).catch(function (err) {
    // Suppress unhandled promise rejection if endpoint is unavailable or in test environment
});

// Fetch Firebase configuration details
rpc("/firebase_config_details", {}).then(function (data) {
    if (data) {
        const json = JSON.parse(data);
        vapid = json.vapid;
        firebaseConfig = json.config;
        // Initialize Firebase app with the retrieved configuration
        if (typeof firebase !== 'undefined' && firebase.apps && !firebase.apps.length) {
            firebase.initializeApp(firebaseConfig);
        }
        if (typeof firebase !== 'undefined' && firebase.messaging) {
            messaging = firebase.messaging();
        }

        // Function to request notification permission and retrieve token
        function requestPermissionAndRetrieveToken() {
            Notification.requestPermission().then((permission) => {
                if (permission === 'granted') {
                    // Retrieve registration token
                    if (messaging) {
                        messaging.getToken({ vapidKey: vapid }).then((currentToken) => {
                            if (currentToken) {
                                // Send the token to the server for subscription
                                rpc("/push_notification", { name: currentToken }).then(function (response) {
                                }).catch(function (error) {
                                    console.warn('Failed to send token to server:', error);
                                });
                            } else {
                                console.warn('No registration token available');
                            }
                        }).catch((err) => {
                            console.warn('Error retrieving token:', err);
                        });
                    }
                } else {
                    console.warn('Permission for notifications was denied');
                }
            }).catch((err) => {
                console.warn('Unable to get permission to notify:', err);
            });
        }

        // Initialize Firebase messaging and handle incoming messages
        if (messaging) {
            messaging.onMessage((payload) => {
                // Show notification to user
                const notificationTitle = payload.notification.title;
                const notificationOptions = {
                    body: payload.notification.body,
                    icon: payload.notification.icon
                };
                navigator.serviceWorker.getRegistrations().then((registrations) => {
                    if (registrations && registrations.length > 0) {
                        registrations[0].showNotification(notificationTitle, notificationOptions);
                    }
                }).catch((err) => {
                    console.warn('Error showing notification:', err);
                });
            });
        }

        // Request permission and retrieve token
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                requestPermissionAndRetrieveToken();
            });
        } else {
            requestPermissionAndRetrieveToken();
        }
    }
}).catch(function (err) {
    // Suppress unhandled promise rejection if endpoint is unavailable or in test environment
});
