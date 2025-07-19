/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {Orderline} from "@point_of_sale/app/generic_components/orderline/orderline";
import {useService} from "@web/core/utils/hooks";
import {OrderQuestionPopup} from "../../Popups/OrderQuestionPopup";
import {_t} from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useState } from "@odoo/owl";

patch(Orderline.prototype, {
    setup() {
        super.setup(...arguments);
        this.state = useState({
            question_list : []
        })
        this.notification = useService("notification");
        this.popup = useService("dialog");
        this.pos = usePos();
    },
    AddOptions() {
        var ProductQuestions = this.props.slots["product-name"].__ctx.line.product_id.product_tmpl_id.order_question_ids
        var OrderQuestions = this.env.services.pos.order_questions
        let question = [];
        for (var i = 0, len = OrderQuestions.length; i < len; i++) {
            for (var j = 0, leng = ProductQuestions.length; j < leng; j++) {
                if (OrderQuestions[i].id == ProductQuestions[j].id) {
                    question.push({
                    id: OrderQuestions[i].id,
                    name: OrderQuestions[i].name
                    });
                }
            }
        }
        if (question.length !== 0) {
            const questionText = question.map(q => `${q.name}`).join('\n');
            this.popup.add(OrderQuestionPopup, {
                title: _t("Extra..."),
                confirmClass: "btn-primary",
                body: questionText,

            });
        } else {
             this.popup.add(ConfirmationDialog, {
                title: _t("Add Options to Select..."),
                body: _t("here is no options added for this product."),
                confirmLabel: _t("Ok"),
                confirm: () => {
                this.popup.closeAll();
                }
            });
        }
    },
});
