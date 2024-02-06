/** @odoo-module **/
import { useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { OrderSummaryReceiptScreen } from "./OrderReceiptPopup";

    export class OrderSummaryPopup extends AbstractAwaitablePopup {
    // Extending AbstractAwaitablePopup And Adding A Popup
        setup() {
            super.setup();
            this.pos = usePos();
            this.orm = useService("orm");
            this.is_session = useRef("isSession");
            this.date_section = useRef("dateSection");
            this.state = useState({
                current_session: false,
                start_date: "",
                end_date: "",
                status: '' || 'draft' || 'paid' || 'done' || 'invoiced' || 'cancel',
            });
        }
        async click_is_session(){
            // Check if the session is enabled or not
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
            // Get order summary
            var is_session = this.state.current_session;
            var start_date = this.state.start_date || '';
            var end_date = this.state.end_date || '';
            var status = this.state.status;
            var self = this;
            var order = this.pos.get_order()['sequence_number']
            var domain = []
            if(is_session){
                domain = [['session_id', '=', this.pos.pos_session.id]]
                if(status){
                    domain = [['session_id', '=', this.pos.pos_session.id], ['state', '=', status]]
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
                if(status){
                    domain = [['date_order', '>=', start_date + ' 00:00:00'],
                          ['date_order', '<=', end_date +  ' 23:59:59'],
                          ['state', '=', status]]
                }
            }
                var orders_ids = await this.orm.call('pos.order','search', [domain]);
                var order_ids = []
               orders_ids.forEach(function(value, index) {
                     order_ids.push(value);
               });
                var orders = await this.orm.call('pos.order', 'get_order_summary', [order, order_ids]);
                if (orders.length != 0){
                    const { confirmed } = await this.pos.popup.add(OrderSummaryReceiptScreen,
                        {orders: orders, start_date: start_date, end_date: end_date, data: this.pos}
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
OrderSummaryPopup.template = 'OrderSummaryPopup';
