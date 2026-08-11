/** @odoo-module */
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { Dialog } from "@web/core/dialog/dialog";
import { useState } from "@odoo/owl";

export class OrderQuestionPopup extends ConfirmationDialog {
    static template = "pos_order_question.ConfirmationDialog";
    static components = { Dialog };
    static props = {
        ...ConfirmationDialog.props,
        line: { type: Object, optional: true },
    };

    setup() {
        super.setup();
        this.pos = usePos();
        const initialQuestions = this.props.line.question_list ? this.props.line.question_list.split(',') : [];
        this.state = useState({
            QuestionList: initialQuestions
        });
    }
     /**
     * Handles checkbox selection changes.
     */
    changeCheckBox(ev) {
        const value = ev.target.dataset.value;
        if (ev.target.checked) {
            this.state.QuestionList.push(value);
        } else {
            const index = this.state.QuestionList.indexOf(value);
            if (index !== -1) {
                this.state.QuestionList.splice(index, 1); // Remove the unchecked value
            }
        }
    }

    getPayload() {
        const line = this.props.line;
        if (line) {
            line.setQuestionList(this.state.QuestionList);
        }
    }

    async confirm() {
        if (this.state.QuestionList.length === 0) {
            this.env.services.notification.add(
                "Please select at least one option before proceeding.",
                { type: "warning" }
            );
            return;
        }
        this.getPayload();
        this.props.close();
    }
}
