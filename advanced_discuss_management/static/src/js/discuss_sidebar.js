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
});
DiscussSidebar.components = {
    ...DiscussSidebar.components,
    DiscussSidebarMailboxes, DiscussSidebarCategories
};
