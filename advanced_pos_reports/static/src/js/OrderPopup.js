/** @odoo-module **/
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { Component, useState, useRef } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog, AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { OrderSummaryReceiptScreen } from "./OrderReceiptPopup";

    export class OrderSummaryPopup extends Component {
        static components = { Dialog };
        static template = 'OrderSummaryPopup';
        static props = {
            title:{ type: String} ,
            close: "Cancel",
        }

        setup() {
            super.setup();
            this.pos = usePos();
            this.orm = useService("orm");
            this.is_session = useRef("isSession");
            this.dialog = useService("dialog");
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
            var order = this.pos.getOrder()['sequence_number']
            var domain = []
            if(is_session){
                domain = [['session_id', '=', this.pos.config.current_session_id.id]]
                if(status){
                    domain = [['session_id', '=', this.pos.config.current_session_id.id], ['state', '=', status]]
                }
            }

            else{
                 if (start_date.trim() === '' || end_date.trim() === '') {
                     return;
                 }
                 if (start_date > end_date) {
                     this.dialog.add(AlertDialog, {
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
                    const { confirmed } = await this.dialog.add(OrderSummaryReceiptScreen,
                        {orders: orders, start_date: start_date, end_date: end_date, data: this.pos}
                      );
                    }
                else {
                    await this.dialog.add(AlertDialog, {
                        title: "No Data",
                        body: "No Data Available .",
                    });
                }
        }
    }
