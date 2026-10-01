/** @odoo-module **/
import { Component } from "@odoo/owl";

export class AiLoadingModal extends Component {
    static template = "ai_loading_dashboard.AiLoadingModal";

    static props = {
         visible:  { type: Boolean, optional: true },
        message:  { type: String,  optional: true },
        progress: { type: Number,  optional: true },
    };

    static defaultProps = {
        visible:  false,
        message:  "Thinking through your request",
        progress: 0,
    };
}