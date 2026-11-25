/** @odoo-module **/

if (typeof window !== "undefined" && !window.exports) {
    window.exports = {};
}

import { Component, proxy } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class VoiceAssistantSystray extends Component {
    static template = "ora_ai_base.VoiceAssistantSystray";
    static components = { Dropdown, DropdownItem };

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.state = proxy({
            assistants: [],
            loading: false,
        });
    }

    async onBeforeOpen() {
        this.state.loading = true;
        try {
            this.state.assistants = await this.orm.call("ora.ai", "get_available_assistants", []);
        } catch (e) {
            console.error("Failed to fetch voice assistants:", e);
        } finally {
            this.state.loading = false;
        }
    }

    async openAssistant(assistant) {
        if (!assistant) {
            return;
        }
        const currentUserId =
            (typeof odoo !== "undefined" && odoo.session_info?.uid) ||
            window.odoo?.session_info?.uid ||
            this.env?.services?.user?.userId ||
            this.env?.services?.user?.id ||
            null;
        await this.action.doAction({
            type: "ir.actions.client",
            tag: "action_voice_assistant",
            target: "new",
            name: assistant.name ? `Voice Assistant: ${assistant.name}` : "Voice Assistant",
            context: { dialog_size: "extra-large" },
            params: {
                assistant_id: assistant.assistant_id,
                api_key: assistant.api_key,
                assistant_name: assistant.name,
                provider: assistant.provider,
                provider_model: assistant.provider_model,
                language: assistant.language,
                transcriber: assistant.transcriber,
                user_id: currentUserId,
            },
        });
    }

    manageAssistants() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Voice Assistants",
            res_model: "ora.ai",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }
}

registry.category("systray").add("ora_ai_base.VoiceAssistantSystray", {
    Component: VoiceAssistantSystray,
}, { sequence: 25 });
