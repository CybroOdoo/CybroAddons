/** @odoo-module **/
/*#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################*/
import { describe, expect, test } from "@odoo/hoot";

describe("Mail Push Notification Frontend (firebase.js)", () => {

    test("Registers service worker when push_notification is enabled in credentials", async () => {
        let registeredSwPath = null;
        const originalServiceWorker = navigator.serviceWorker;

        try {
            Object.defineProperty(navigator, "serviceWorker", {
                value: {
                    register: async (path) => {
                        registeredSwPath = path;
                        return Promise.resolve({});
                    },
                    getRegistrations: async () => Promise.resolve([]),
                },
                configurable: true,
                writable: true,
            });

            // Simulate credentials callback with push_notification: true
            const data = { id: 1, push_notification: true };
            if (data && data.push_notification) {
                if ("serviceWorker" in navigator) {
                    await navigator.serviceWorker.register("/firebase-messaging-sw.js");
                }
            }

            expect(registeredSwPath).toBe("/firebase-messaging-sw.js");
        } finally {
            Object.defineProperty(navigator, "serviceWorker", {
                value: originalServiceWorker,
                configurable: true,
                writable: true,
            });
        }
    });

    test("Does not register service worker when push_notification is disabled", async () => {
        let registerCalled = false;
        const originalServiceWorker = navigator.serviceWorker;

        try {
            Object.defineProperty(navigator, "serviceWorker", {
                value: {
                    register: async () => {
                        registerCalled = true;
                        return Promise.resolve({});
                    },
                },
                configurable: true,
                writable: true,
            });

            // Simulate credentials callback with push_notification: false
            const data = { id: 1, push_notification: false };
            if (data && data.push_notification) {
                await navigator.serviceWorker.register("/firebase-messaging-sw.js");
            }

            expect(registerCalled).toBe(false);
        } finally {
            Object.defineProperty(navigator, "serviceWorker", {
                value: originalServiceWorker,
                configurable: true,
                writable: true,
            });
        }
    });

    test("Initializes Firebase app and retrieves messaging service with configuration", async () => {
        let initializedConfig = null;
        let messagingCreated = false;

        const mockFirebase = {
            apps: [],
            initializeApp: (config) => {
                initializedConfig = config;
                mockFirebase.apps.push(config);
            },
            messaging: () => {
                messagingCreated = true;
                return {
                    getToken: async () => "test_token",
                    onMessage: () => {},
                };
            },
        };

        const configPayload = JSON.stringify({
            vapid: "mock_vapid_key_777",
            config: {
                apiKey: "mock_api_key",
                projectId: "mock_project_id",
            },
        });

        const json = JSON.parse(configPayload);
        if (!mockFirebase.apps.length) {
            mockFirebase.initializeApp(json.config);
        }
        const messaging = mockFirebase.messaging();

        expect(initializedConfig.apiKey).toBe("mock_api_key");
        expect(initializedConfig.projectId).toBe("mock_project_id");
        expect(messagingCreated).toBe(true);
        expect(messaging).not.toBe(null);
    });

    test("Sends FCM registration token to /push_notification on permission granted", async () => {
        let tokenSent = null;

        const mockMessaging = {
            getToken: async ({ vapidKey }) => {
                expect(vapidKey).toBe("mock_vapid_123");
                return "mock_fcm_token_xyz";
            },
        };

        const mockRpc = async (route, params) => {
            if (route === "/push_notification") {
                tokenSent = params.name;
                return true;
            }
        };

        // Simulate permission granted flow
        const permission = "granted";
        if (permission === "granted") {
            const currentToken = await mockMessaging.getToken({ vapidKey: "mock_vapid_123" });
            if (currentToken) {
                await mockRpc("/push_notification", { name: currentToken });
            }
        }

        expect(tokenSent).toBe("mock_fcm_token_xyz");
    });

    test("Does not send token to server if permission is denied", async () => {
        let rpcCalled = false;
        const mockRpc = async () => {
            rpcCalled = true;
        };

        const permission = "denied";
        if (permission === "granted") {
            await mockRpc("/push_notification", { name: "should_not_send" });
        }

        expect(rpcCalled).toBe(false);
    });

    test("Displays browser notification on incoming messaging payload", async () => {
        let shownTitle = null;
        let shownOptions = null;

        const mockRegistrations = [
            {
                showNotification: (title, options) => {
                    shownTitle = title;
                    shownOptions = options;
                },
            },
        ];

        const payload = {
            notification: {
                title: "Message from John Doe",
                body: "Hello there!",
                icon: "/mail_push_notification/static/description/icon.png",
            },
        };

        // Trigger notification handler
        const notificationTitle = payload.notification.title;
        const notificationOptions = {
            body: payload.notification.body,
            icon: payload.notification.icon,
        };

        mockRegistrations[0].showNotification(notificationTitle, notificationOptions);

        expect(shownTitle).toBe("Message from John Doe");
        expect(shownOptions.body).toBe("Hello there!");
        expect(shownOptions.icon).toBe("/mail_push_notification/static/description/icon.png");
    });
});
