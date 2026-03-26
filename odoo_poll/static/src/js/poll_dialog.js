/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";

export class PollDialog extends Component {
    static template = "odoo_poll.PollDialog";
    static components = { Dialog };
    static props = {
        threadId: Number,
        threadModel: String,
        close: Function,
        onPollCreated: { type: Function, optional: true },
    };

    setup() {
        this.notification = useService("notification");

        this.state = useState({
            question: "",
            options: ["", ""],
            isMultipleChoice: false,
        });
    }

    //Add a new empty option field
    addOption() {
        this.state.options.push("");
    }

    //Remove an option by index
    removeOption(index) {
        if (this.state.options.length > 2) {
            this.state.options.splice(index, 1);
        }
    }

    //Update option value at given index
    updateOption(index, value) {
        this.state.options[index] = value;
    }

    //Creates poll
    async createPoll() {
        if (!this.state.question.trim()) {
            this.notification.add("Please enter a question", { type: "warning" });
            return;
        }

        const validOptions = this.state.options.filter(o => o.trim());
        if (validOptions.length < 2) {
            this.notification.add("Please add at least 2 options", { type: "warning" });
            return;
        }

        try {
            await rpc("/discuss/poll/create", {
                thread_id: this.props.threadId,
                thread_model: this.props.threadModel,
                question: this.state.question,
                options: validOptions,
                is_multiple_choice: this.state.isMultipleChoice,
                company_id: user.context.company_id || (user.context.allowed_company_ids ? user.context.allowed_company_ids[0] : null),
                context: user.context,
            });

            this.notification.add("Poll created successfully!", { type: "success" });

            if (this.props.onPollCreated) {
                this.props.onPollCreated();
            }

            this.props.close();
        } catch (error) {
            console.error("Error creating poll:", error);
            this.notification.add("Failed to create poll. Please try again.", { type: "danger" });
        }
    }
}

// Register in registry so other modules can access without direct import
registry.category("discuss.poll_components").add("PollDialog", PollDialog);
