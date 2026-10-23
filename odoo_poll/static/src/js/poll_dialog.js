import { Component, proxy } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { _t } from "@web/core/l10n/translation";

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
        this.title = _t("Create a Poll");
        this.notification = useService("notification");

        this.state = proxy({
            question: "",
            options: ["", ""],
            isMultipleChoice: false,
        });
    }

    addOption() {
        this.state.options.push("");
    }

    removeOption(index) {
        if (this.state.options.length > 2) {
            this.state.options.splice(index, 1);
        }
    }

    updateOption(index, value) {
        this.state.options[index] = value;
    }

    async createPoll() {
        if (!this.state.question.trim()) {
            this.notification.add(_t("Please enter a question"), { type: "warning" });
            return;
        }

        const validOptions = this.state.options.filter(o => o.trim());
        if (validOptions.length < 2) {
            this.notification.add(_t("Please add at least 2 options"), { type: "warning" });
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

            this.notification.add(_t("Poll created successfully!"), { type: "success" });

            if (this.props.onPollCreated) {
                this.props.onPollCreated();
            }

            this.props.close();
        } catch (error) {
            this.notification.add(_t("Failed to create poll. Please try again."), { type: "danger" });
        }
    }
}

registry.category("discuss.poll_components").add("PollDialog", PollDialog);