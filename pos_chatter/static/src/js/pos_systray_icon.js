/** @odoo-module **/
import { Component, useRef, onWillUnmount } from "@odoo/owl";
import { mount } from "@odoo/owl";
import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { PosMsgView } from "./pos_msg_view";
import { rpc } from "@web/core/network/rpc";
import { useState } from "@odoo/owl";

patch(Navbar.prototype, {
    setup() {
        super.setup();
        this.message = useRef('root');
        this.state = useState({
            messageCount: 0,
        });
        this.schedule_dropdown = null;
        this.refreshInterval = null;

        // Initial fetch
        this.fetchMessageCount();

        // Set up interval for refreshing every 5 seconds
        this.setupRefreshInterval();

        // Clean up interval on component destruction
        onWillUnmount(() => {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
        });
    },

    setupRefreshInterval() {
        // Refresh every 5 seconds (5000 milliseconds)
        this.refreshInterval = setInterval(() => {
            this.fetchMessageCount();
        }, 5000);
    },

    async fetchMessageCount() {
        try {
            const data = await rpc("/pos_systray/message_data");
            const message_list = data.map((message) => ({
                id: message.id,
                type: message.type,
                name: message.name,
                message_body: new DOMParser().parseFromString(message.message_body, "text/html").documentElement.textContent,
                count: message.count || 0,
            }));
            const totalCount = message_list.reduce((sum, msg) => sum + msg.count, 0);
            this.state.messageCount = totalCount;
        } catch (error) {
            console.error("Failed to fetch message count:", error);
        }
    },

    onClick(ev) {
        const systrayElements = document.querySelectorAll(".pos_systray_template");
        if (systrayElements.length === 0) {
            this.schedule_dropdown = mount(PosMsgView, document.body);
        } else {
            this.schedule_dropdown?.then((res) => {
                res.__owl__.remove();
            });
        }
    },
});