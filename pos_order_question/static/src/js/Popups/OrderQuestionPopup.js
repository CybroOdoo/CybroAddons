/** @odoo-module */
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Dialog } from "@web/core/dialog/dialog";
import { useState } from "@odoo/owl";

export class OrderQuestionPopup extends ConfirmationDialog {
    static template = "pos_order_question.ConfirmationDialog";
    static components = { Dialog };

    setup() {
        super.setup();
        this.pos = usePos();
        this.state = useState({
            QuestionList: []
        });
    }

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
        if(this.pos.get_order().get_selected_orderline()) {
            this.pos.get_order().get_selected_orderline().QuestionList = this.state.QuestionList;
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

        this.props.close(this.getPayload());
    }
}
