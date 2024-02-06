/** @odoo-module **/
import { useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { PaymentSummaryReceiptScreen } from "./PaymentReceiptPopup";

    export class PaymentSummaryPopup extends AbstractAwaitablePopup {
    // Extending AbstractAwaitablePopup And Adding A Popup
        setup() {
            super.setup();
            this.pos = usePos();
            this.orm = useService("orm");
            this.is_session = useRef("isSession")
            this.date_section = useRef("dateSection")
            this.state = useState({
                current_session: false,
                start_date: "",
                end_date: "",
                summary: '' || 'sales_person' || 'journal',
            });
        }
        async click_is_session(){
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
            var order = this.pos.get_order()['sequence_number']
            var is_user = false;
            if(summary_type === 'sales_person'){
                is_user = true
            }
            var domain = []
            if(is_session){
                domain = [['session_id', '=', this.pos.pos_session.id]]
                if(summary_type == 'sales_person'){
                    domain = [['session_id', '=', this.pos.pos_session.id], ['user_id', '=', this.pos.user.id]]
                }
            }
            else{
                 if (start_date.trim() === '' || end_date.trim() === '') {
                     return;
                 }
                 if (start_date > end_date) {
                     this.pos.popup.add(ErrorPopup, {
                         title: "Error",
                         body: "Start Date Greater than End Date .",
                     });
                     return;
                 }
                domain = [['date_order', '>=', start_date + ' 00:00:00'],
                          ['date_order', '<=', end_date +  ' 23:59:59']]
                if(summary_type == 'sales_person'){
                    domain = [['date_order', '>=', start_date + ' 00:00:00'],
                              ['date_order', '<=', end_date +  ' 23:59:59'],
                              ['user_id', '=', this.pos.user.id]]
                }
            }
                var orders = await this.orm.call('pos.order', 'search', [domain]);
                var order_ids = []
                orders.forEach(function(value, index) {
                       order_ids.push(value);
                });
                var payment_summary = await this.orm.call('pos.payment', 'get_payment_summary', [order, order_ids]);
                if (payment_summary.length != 0){
                    const { confirmed } = await this.pos.popup.add(PaymentSummaryReceiptScreen,
                        {payment_summary: payment_summary, start_date: start_date, end_date: end_date, is_user: is_user, data: this.pos}
                      );
                    }
                else {
                    await this.pos.popup.add(ErrorPopup, {
                        title: "No Data",
                        body: "No Data Available .",
                    });
                }
        }
    }
PaymentSummaryPopup.template = 'PaymentSummaryPopup';
