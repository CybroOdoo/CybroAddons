/**
 * Odoo module for handling Firebase push notifications.
 *
 * This module initializes Firebase messaging and handles push notifications
 * for the current session's company. It also registers the service worker for
 * handling notifications if the company has push notifications enabled.
 *
 * @module mail_push_notification
 */
odoo.define("mail_push_notification.Firebase", function (require) {
    "use strict";
    var ajax = require('web.ajax');
    var rpc = require("web.rpc");
    var session = require('web.session');
    var vapid = '';
    var firebaseConfig = {};
    var push_notification = false;
    /**
     * Sends an RPC query to retrieve push notification settings for the current company.
     *
     * @function
     * @returns {Promise} A promise that resolves with the push notification settings.
     */
    rpc.query({
        model: 'res.company',
        method: 'search_read',
        fields: ['push_notification'],
        domain: [['id', '=', session.company_id]]
    }, { async: false }).then(function (data) {
        if (data) {
            _.each(data, function (company) {
                if (company.push_notification) {
                    push_notification = true;
                    if ("serviceWorker" in navigator) {
                        navigator.serviceWorker.register("/firebase-messaging-sw.js").then(function () {});
                    }
                }
            });
        }
    });
    ajax.jsonRpc("/firebase_config_details", 'call', {}).then(function (data) {
        if (data) {
            var json = JSON.parse(data);
            vapid = json.vapid;
            firebaseConfig = json.config;
            /**
             * Initializes Firebase messaging and sets up event listeners for incoming messages.
             *
             * @function
             */
            firebase.initializeApp(firebaseConfig);
            const messaging = firebase.messaging();
            /**
             * Handles incoming push notification messages.
             *
             * @function
             * @param {Object} payload - The notification payload.
             */
            messaging.onMessage((payload) => {
                const notificationOptions = {
                    body: payload.notification.body,
                };
                let notification = payload.notification;
                navigator.serviceWorker.getRegistrations().then((registration) => {
                    registration[0].showNotification(notification.title, notificationOptions);
                });
            });
            /**
             * Requests permission for receiving push notifications and retrieves the registration token.
             *
             * @function
             */
            messaging.requestPermission().then(function () {
            /**
             * Retrieves the registration token and sends it to the server for subscription.
             *
             * @function
             * @param {string} vapidKey - The VAPID key for authentication.
             */
                messaging.getToken({ vapidKey: vapid }).then((currentToken) => {
                    if (currentToken) {
                        /**
                         * Sends a POST request to the server with the registration token.
                         *
                         * @function
                         * @param {string} token - The registration token.
                         */
                        $.post("/push_notification", {
                            name: currentToken
                        });
                    } else {
                        console.log('No registration token found');
                    }
                }).catch((err) => {
                    console.log('There is an error has occurred while attempting to retrieve the token.', err);
                });
            });
        }
    });
});
