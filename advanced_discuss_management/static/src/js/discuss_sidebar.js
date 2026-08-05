/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { DiscussSidebar } from "@mail/core/public_web/discuss_sidebar";
import { DiscussSidebarMailboxes } from "@mail/core/web/discuss_sidebar_mailboxes";
import { onMounted, useRef, onWillDestroy } from "@odoo/owl";
import { useState } from "@odoo/owl";
import { DiscussSidebarCategories } from "@mail/discuss/core/public_web/discuss_sidebar_categories";

patch(DiscussSidebar.prototype, {
    setup() {
        super.setup();
        this.root = useRef("root");
        this.onHideChat = () => {
            if (this.root.el) {
                const channelEl = this.root.el.querySelector('.channel');
                if (channelEl) channelEl.classList.add("d-none");
                const mailEl = this.root.el.querySelector('.mail');
                if (mailEl) mailEl.classList.add("d-none");
                const chatEl = this.root.el.querySelector('.chat');
                if (chatEl) chatEl.classList.add("d-none");
            }
        };
        this.env.bus.addEventListener("HIDE:CHAT", this.onHideChat);
        onWillDestroy(() => {
            this.env.bus.removeEventListener("HIDE:CHAT", this.onHideChat);
        });
        this.state = useState({ sidebar: 'channels', chat: 'chats' });
        onMounted(() => {
            // Call the _onClickChannel function when the component is mounted
            this.sidebar;
            if (this.root.el) {
                this._onClickChannel();
            }
        });
    },
    _onClickMail(ev) {
        // Click function of mail button
        const el = this.root.el;
        if (el) {
            el.querySelector('.channel')?.classList.add("d-none");
            el.querySelector('.chat')?.classList.add("d-none");
            el.querySelector('.mail')?.classList.remove("d-none");
        }
        if (this.store && this.store.inbox) {
            this.store.inbox.setAsDiscussThread();
        }
    },
    _onClickChat(ev) {
        // Click function of chat button
        if (this.root.el) {
            const chatEl = this.root.el.querySelector('.chat');
            if (chatEl) chatEl.classList.remove("d-none");
            const mailEl = this.root.el.querySelector('.mail');
            if (mailEl) mailEl.classList.add("d-none");
            const channelEl = this.root.el.querySelector('.channel');
            if (channelEl) channelEl.classList.add("d-none");
        }
        if (this.store && this.store.discuss) {
            this.store.discuss.thread = undefined;
        }
        this.state.sidebarChannel = 'chat';
    },
    _onClickChannel(ev) {
        // Click function of channel button
        if (this.root.el) {
            const channelEl = this.root.el.querySelector('.channel');
            if (channelEl) channelEl.classList.remove("d-none");
            const mailEl = this.root.el.querySelector('.mail');
            if (mailEl) mailEl.classList.add("d-none");
            const chatEl = this.root.el.querySelector('.chat');
            if (chatEl) chatEl.classList.add("d-none");
        }
        if (this.store && this.store.discuss) {
            this.store.discuss.thread = undefined;
        }
        this.state.sidebarChat = 'channel';
    },
    async _onClickMeeting(ev) {
        // First check for camera permissions
        try {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                alert("Camera access is only available on secure connections (HTTPS) or localhost. Please check your URL.");
                return;
            }
            // Requesting access will trigger the browser's "Ask" prompt if not already decided
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            // Close stream immediately as we just needed to verify permission
            stream.getTracks().forEach(track => track.stop());
            
            // If we reached here, we have permission. Proceed with Odoo meeting
            this.store.startMeeting();
        } catch (err) {
            if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
                alert("Camera access was denied. Please enable it in your browser settings to start a meeting.");
            } else {
                console.error("Camera error:", err);
                // Still try to start meeting, maybe Odoo's internal logic handles it differently
                this.store.startMeeting();
            }
        }
    },
});
DiscussSidebar.components = {
    ...DiscussSidebar.components,
    DiscussSidebarMailboxes, DiscussSidebarCategories
};
