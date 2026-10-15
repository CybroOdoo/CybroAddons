import { registry } from "@web/core/registry";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { Component } from "@odoo/owl";
import { AiChatPanel } from "../chat_panel/chat_panel";

/**
 * Full screen chat with the AI assistant, with the list of the conversations.
 */
export class AiChatAction extends Component {
    static template = "ai_chat_pro.ChatAction";
    static components = { AiChatPanel };
    static props = {
        ...standardActionServiceProps,
        // a question asked to the voice assistant of the systray, asked in a new chat
        voiceQuestion: { type: Object, optional: true },
    };

    /**
     * The conversation to open, given by a link (the note of an activity planned from an
     * analysis): /odoo/action-ai_chat_pro.ai_chat_action_client?active_id=42
     */
    get conversationId() {
        const action = this.props.action || {};
        return parseInt(action.context?.active_id || action.params?.conversation_id, 10) || false;
    }
}

registry.category("actions").add("ai_chat_pro.chat", AiChatAction);
