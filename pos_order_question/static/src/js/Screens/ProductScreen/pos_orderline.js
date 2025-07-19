/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

// Patch the PosOrderline to store the QuestionList in the order line state
patch(PosOrderline.prototype, {
    setup() {
        super.setup(...arguments);

        // Initialize QuestionList in state
        this.QuestionList = this.QuestionList || [];
    },

    // Method to update the QuestionList state dynamically
    setQuestionList(questions) {
        this.QuestionList = questions;
        this.trigger("change", { QuestionList: this.QuestionList }); // Ensure UI updates
    },

    serialize(options = {}) {
        const json = super.serialize(...arguments);
        json.question_list = this.QuestionList.join(',');
        this.storedQuestionList = json.question_list;
        console.log("json.question_list",json.question_list)
        return json;
    },


    getDisplayData() {
        return {
            ...super.getDisplayData(),
            OrderQuestion: this.QuestionList.join('/'),
        };
    },
});

// Update the Orderline component's props to accept the QuestionList
Orderline.props = {
    ...Orderline.props,
    line: {
        ...Orderline.props.line,
        shape: {
            ...Orderline.props.line.shape,
            OrderQuestion: { type: String, optional: true },
        }
    }
};
