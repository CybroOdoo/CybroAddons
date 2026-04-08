/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {Orderline} from "@point_of_sale/app/generic_components/orderline/orderline";
import {useService} from "@web/core/utils/hooks";
import {OrderQuestionPopup} from "../../Popups/OrderQuestionPopup";
import {_t} from "@web/core/l10n/translation";
patch(Orderline.prototype, {
    setup() {
        super.setup(...arguments);
        // Use the nomenclature's separaor regex, else use an impossible one.
        this.popup = useService("popup");
    },
    AddOptions() {
        var ProductQuestions = this.props.slots.default.__ctx.line.product.order_question_ids
        var OrderQuestions = this.env.services.pos.order_questions
        let question = [];
        for (var i = 0, len = OrderQuestions.length; i < len; i++) {
            for (var j = 0, leng = ProductQuestions.length; j < leng; j++) {
                if (OrderQuestions[i].id === ProductQuestions[j]) {
                    question.push(OrderQuestions[i].name)
                }
            }
        }
        if (question.length !== 0) {
            this.popup.add(OrderQuestionPopup, {
                title: _t("Extra..."), confirmText: 'Ok',
                cancelText: 'Cancel',
                body: question,
            });
        } else {
            this.popup.add(OrderQuestionPopup, {
                title: _t("Add Options to Select..."),
                confirmText: 'Ok',
                cancelText: 'Cancel',

            });

        }
    },
});
