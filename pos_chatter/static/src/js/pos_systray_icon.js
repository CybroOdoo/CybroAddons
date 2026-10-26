import { onWillUnmount, proxy } from "@odoo/owl";
import { Navbar } from "@point_of_sale/app/components/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { PosMsgView } from "./pos_msg_view";
import { ChatMsgView } from "./pos_chat_view";
import { rpc } from "@web/core/network/rpc";
Object.assign(Navbar.components, {
    PosMsgView,
    ChatMsgView,
});

let isPageNavigating = false;
window.addEventListener("beforeunload", () => {
    isPageNavigating = true;
});
window.addEventListener("pagehide", () => {
    isPageNavigating = true;
});

patch(Navbar.prototype, {
    setup() {
        super.setup();
        this.chatterState = proxy({
            messageCount: 0,
            isOpen: false,
            activeChannelId: null,
        });
        this.refreshInterval = null;

        // Initial fetch
        this.fetchMessageCount();

        // Set up interval for refreshing every 5 seconds
        this.setupRefreshInterval();

        // Clean up interval on component destruction
        onWillUnmount(() => {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
                this.refreshInterval = null;
            }
        });
    },

    setupRefreshInterval() {
        this.refreshInterval = setInterval(() => {
            this.fetchMessageCount();
        }, 5000);
    },

    get isScreensaver() {
        const screen = this.pos?.router?.currentScreen?.();
        return ["SaverScreen", "LoginScreen"].includes(screen);
    },

    async fetchMessageCount() {
        if (isPageNavigating || this.isScreensaver) {
            return;
        }
        try {
            const data = await rpc("/pos_systray/message_data");
            const totalCount = (data || []).reduce((sum, msg) => sum + (msg.count || 0), 0);
            this.chatterState.messageCount = totalCount;
        } catch (error) {
            if (!isPageNavigating && error?.name !== "ConnectionLostError") {
                console.error("Failed to fetch message count:", error);
            }
        }
    },

    onChatterClick() {
        this.chatterState.isOpen = !this.chatterState.isOpen;
    },

    openChat(channelId) {
        this.chatterState.isOpen = false;
        this.chatterState.activeChannelId = channelId;
    },

    closeChat() {
        this.chatterState.activeChannelId = null;
        this.fetchMessageCount();
    },

    closeMsgView() {
        this.chatterState.isOpen = false;
    },

    noOpenDialogs() {
        if (!this.isScreensaver && (this.chatterState?.activeChannelId || this.chatterState?.isOpen)) {
            return false;
        }
        return super.noOpenDialogs();
    },
});
