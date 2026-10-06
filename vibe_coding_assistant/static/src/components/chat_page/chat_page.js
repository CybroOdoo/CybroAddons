/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ConversationList } from "../conversation_list/conversation_list";
import { MessageThread } from "../message_thread/message_thread";
import { Composer } from "../composer/composer";
import { FileTree } from "../file_tree/file_tree";
import { CodeViewer } from "../code_viewer/code_viewer";

export class ChatPage extends Component {
    static template = "vibe_coding_assistant.ChatPage";
    static components = { ConversationList, MessageThread, Composer, FileTree, CodeViewer };

    setup() {
        this.vibeStore = useService("vibeStore");
        this.actionService = useService("action");
        this.storeState = useState(this.vibeStore.state);
        this.state = useState({ rechecking: false });

        onWillStart(async () => {
            await Promise.all([
                this.vibeStore.loadProviderInfo(),
                this.vibeStore.loadConversations(),
                this.vibeStore.loadPromptTemplates(),
            ]);
        });

        this._onFocus = () => {
            if (this.storeState.providerInfo === false) {
                this.vibeStore.loadProviderInfo();
            }
        };
        onMounted(() => {
            window.addEventListener("focus", this._onFocus);
        });
        onWillUnmount(() => {
            window.removeEventListener("focus", this._onFocus);
        });
    }

    get hasProvider() {
        return !!this.storeState.providerInfo;
    }

    get providerLoaded() {
        return this.storeState.providerInfo !== null;
    }

    goToSettings() {
        this.actionService.doAction("vibe_coding_assistant.action_my_ai_config");
    }

    /** Manual escape hatch — user clicks "Recheck" in the no-provider card. */
    async recheckProvider() {
        if (this.state.rechecking) return;
        this.state.rechecking = true;
        try {
            await this.vibeStore.loadProviderInfo();
        } finally {
            this.state.rechecking = false;
        }
    }
}

registry.category("actions").add("vibe_coding_assistant.chat_page", ChatPage);
