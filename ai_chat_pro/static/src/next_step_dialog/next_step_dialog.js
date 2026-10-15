import { Dialog } from "@web/core/dialog/dialog";
import { Component, useState } from "@odoo/owl";

/**
 * Confirm a next step of a deep analysis to plan as an activity: its summary, type and
 * due date can be changed first.
 */
export class NextStepActivityDialog extends Component {
    static template = "ai_chat_pro.NextStepActivityDialog";
    static components = { Dialog };
    static props = {
        step: String,
        // { summary, activity_type_id, activity_types: [{ id, name, icon, date_deadline }], user_name }
        defaults: Object,
        onConfirm: Function,
        close: Function,
    };

    setup() {
        const type = this.getType(this.props.defaults.activity_type_id);
        this.state = useState({
            summary: this.props.defaults.summary,
            activityTypeId: type?.id || false,
            dateDeadline: type?.date_deadline || "",
            // the due date follows the type, until the user picks one
            isDateChanged: false,
            isSaving: false,
        });
    }

    getType(typeId) {
        return this.props.defaults.activity_types.find((type) => type.id === typeId);
    }

    onTypeChange(ev) {
        const type = this.getType(parseInt(ev.target.value, 10));
        this.state.activityTypeId = type?.id || false;
        if (type && !this.state.isDateChanged) {
            this.state.dateDeadline = type.date_deadline;
        }
    }

    onDateChange(ev) {
        this.state.dateDeadline = ev.target.value;
        this.state.isDateChanged = true;
    }

    get canConfirm() {
        return Boolean(this.state.activityTypeId && this.state.summary.trim() && !this.state.isSaving);
    }

    async confirm() {
        if (!this.canConfirm) {
            return;
        }
        this.state.isSaving = true;
        try {
            await this.props.onConfirm({
                summary: this.state.summary.trim(),
                activity_type_id: this.state.activityTypeId,
                date_deadline: this.state.dateDeadline || false,
            });
            this.props.close();
        } finally {
            this.state.isSaving = false;
        }
    }
}
