/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { AiChatWindow } from "../chat_window/ai_chat_window";

export class AiSystrayItem extends Component {
    setup() {
        this.overlay = useService("overlay");
        this.removeChatOverlay = null;
        this.state = useState({ isOpen: false });
    }

    toggleChat() {
        if (this.removeChatOverlay) {
            this.removeChatOverlay();
            this.removeChatOverlay = null;
            this.state.isOpen = false;
        } else {
            this.state.isOpen = true;
            this.removeChatOverlay = this.overlay.add(
                AiChatWindow,
                { 
                    closeChat: () => this.toggleChat(),
                },
                { 
                    position: "fixed",
                }
            );
        }
    }
}

AiSystrayItem.template = "ai_connector_agent.AiSystrayItem";
AiSystrayItem.components = { AiChatWindow };

export const systrayItem = {
    Component: AiSystrayItem,
};

// Sequence controls the position in the systray
registry.category("systray").add("ai_connector_agent.SystrayItem", systrayItem, { sequence: 100 });
