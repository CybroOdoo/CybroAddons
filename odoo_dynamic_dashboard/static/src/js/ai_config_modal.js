/** @odoo-module **/
import { Component, useState } from "@odoo/owl";

export class AiConfigModal extends Component {
    static template = "ai_loading_dashboard.AiConfigModal";

     static props = {
        visible:   { type: Boolean,  optional: true },
        models:    { type: Array,    optional: true },
        onConfirm: { type: Function, optional: true },
        onCancel:  { type: Function, optional: true },
    };

    static defaultProps = {
        visible: false,
        models:  [],
    };

    setup() {
        this.state = useState({
            selectedModel: "",
            maxCards:      10,
            error:         "",
        });
    }

    // ── Handlers ──────────────────────────────────────

    onModelChange(ev) {
        this.state.selectedModel = ev.target.value;
        this.state.error = "";
    }

    onMaxCardsChange(ev) {
        const val = parseInt(ev.target.value, 10);
        this.state.maxCards = isNaN(val) ? "" : val;
        this.state.error = "";
    }

    onConfirm() {
        // Validate
        if (!this.state.selectedModel) {
            this.state.error = "Please select an Odoo model.";
            return;
        }
        if (!this.state.maxCards || this.state.maxCards < 1) {
            this.state.error = "Please enter a valid number of cards (min 1).";
            return;
        }

        // Pass values up to parent, then reset form
        this.props.onConfirm({
            model:    this.state.selectedModel,
            maxCards: this.state.maxCards,
        });

        this.state.selectedModel = "";
        this.state.maxCards      = 10;
        this.state.error         = "";
    }

    onCancel() {
        this.state.error = "";
        this.props.onCancel();
    }
}