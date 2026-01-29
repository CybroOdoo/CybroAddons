odoo.define('pos_order_question.PosOrderQuestion', function (require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const {_lt} = require('@web/core/l10n/translation');

    class OrderQuestionPopup extends AbstractAwaitablePopup {
        mounted() {
            this.playSound('bell');
        }
        QuestionList = [];
        _onClickCheck(ev) {
            //    This function will work when clicking on checkboxes.It will add questions of enabled check boxed into the list.
            const questionText = ev.target.parentNode.innerText.trim();
            if (ev.target.checked === true) {
                this.QuestionList.push(ev.target.parentNode.innerText)
            } else {
                this.QuestionList = this.QuestionList.filter(item => item !== questionText);
            }
        }
        async confirm() {
            //   This function will work when clicking on ok button in the popup.It will add selected questions into order lines.
            const selectedOrderline = this.env.pos.get_order().get_selected_orderline();
            selectedOrderline.QuestionList = this.QuestionList
            this.cancel();
        }
    }
    OrderQuestionPopup.template = 'OrderQuestionPopup';
    OrderQuestionPopup.defaultProps = {
        confirmText: _lt('Ok'),
        cancelText: _lt('Cancel'),
        title: _lt('Error'),
        body: '',
    };

    Registries.Component.add(OrderQuestionPopup);

    return OrderQuestionPopup;
});
