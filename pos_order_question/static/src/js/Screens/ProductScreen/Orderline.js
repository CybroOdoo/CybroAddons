/** @odoo-module **/
import {patch} from "@web/core/utils/patch";
import {Orderline} from "@point_of_sale/app/components/orderline/orderline";
import {useService} from "@web/core/utils/hooks";
import {OrderQuestionPopup} from "../../Popups/OrderQuestionPopup";
import {_t} from "@web/core/l10n/translation";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {usePos} from "@point_of_sale/app/hooks/pos_hook";

patch(Orderline.prototype, {
    setup() {
        super.setup(...arguments);
        this.popup = useService("dialog");
        this.pos = usePos();
    },
    AddOptions() {
        var ProductQuestions = this.props.slots["pack-lot-icon"].__ctx.line.product_id.product_tmpl_id.order_question_ids
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
                confirmLabel: _t("Confirm"),
                body: questionText,
                line: this.props.line,
            });
        } else {
            this.popup.add(ConfirmationDialog, {
                title: _t("Add Options to Select..."),
                body: _t("There are no options added for this product."),
                confirmLabel: _t("Ok"),
                confirm: () => {
                    this.popup.closeAll();
                }
            });
        }
    },
});
