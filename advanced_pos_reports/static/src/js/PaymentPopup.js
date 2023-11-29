odoo.define('advanced_pos_reports.PaymentSummaryPopup', function(require) {
    'use strict';

    const { useState, useRef } = owl;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { _lt } = require('@web/core/l10n/translation');

    class PaymentSummaryPopup extends AbstractAwaitablePopup {
          /**
            * @Override AbstractAwaitablePopup
          */
        setup() {
            super.setup();
            this.is_session = useRef("isSession")
            this.date_section = useRef("dateSection")
            this.state = useState({
                current_session: false,
                start_date: "",
                end_date: "",
                summary: '' || 'sales_person' || 'journal',
            });
        }
        click_is_session(ev){
            //Check if the current session is enabled or not
            var is_session = this.is_session.el;
            var date_section = this.date_section.el;
            if(is_session.checked){
               date_section.style.display = "none";
            }
            else{
                date_section.style.display = "block";
            }
        }
        async confirm(event) {
            // Get payment summary
            var is_session = this.state.current_session;
            var start_date = this.state.start_date || '';
            var end_date = this.state.end_date || '';
            var summary_type = this.state.summary;
            var order = this.env.pos.get_order()['sequence_number']
            var is_user = false;
            if(summary_type === 'sales_person'){
                is_user = true
            }
            var domain = []
            if(is_session){
                domain = [['session_id', '=', this.env.pos.pos_session.id]]
                if(summary_type == 'sales_person'){
                    domain = [['session_id', '=', this.env.pos.pos_session.id], ['user_id', '=', this.env.pos.user.id]]
                }
            }
            else{
                 if (start_date.trim() === '' || end_date.trim() === '') {
                     return;
                 }
                 if (start_date > end_date) {
                     this.showPopup('ErrorPopup', {
                        title: this.env._t('Error'),
                        body: this.env._t('Start Date Greater than End Date.'),
                     });
                     return;
                 }
                domain = [['date_order', '>=', start_date + ' 00:00:00'],
                          ['date_order', '<=', end_date +  ' 23:59:59']]
                if(summary_type == 'sales_person'){
                    domain = [['date_order', '>=', start_date + ' 00:00:00'],
                              ['date_order', '<=', end_date +  ' 23:59:59'],
                              ['user_id', '=', this.env.pos.user.id]]
                }
            }
                var orders = await this.rpc({
                    model: 'pos.order',
                    method: 'search',
                    args: [domain],
                    });
                var order_ids = []
                orders.forEach(function(value, index) {
                       order_ids.push(value);
                });
                var payment_summary = await this.rpc({
                    model: 'pos.payment',
                    method: 'get_payment_summary',
                    args: [order, order_ids],
                    });
                this.showScreen('PaymentSummaryReceiptScreen', { payment_summary: payment_summary, start_date: start_date, end_date: end_date, is_user: is_user });
                super.confirm();
        }
    }
    PaymentSummaryPopup.template = 'PaymentSummaryPopup';
    PaymentSummaryPopup.defaultProps = {
        confirmText: _lt('Print'),
        cancelText: _lt('Cancel'),
        array: [],
        isSingleItem: false,
    };
    Registries.Component.add(PaymentSummaryPopup);
    return PaymentSummaryPopup;
});
