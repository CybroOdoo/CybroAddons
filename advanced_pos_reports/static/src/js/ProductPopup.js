/** @odoo-module **/
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { Component, useState, useRef } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ProductSummaryReceiptScreen } from "./ProductReceiptPopup";

    export class ProductSummaryPopup extends Component {
    // Extending AbstractAwaitablePopup And Adding A Popup
        static components = { Dialog };
        static template = 'ProductSummaryPopup';
        static props = {
            title:{ type: String} ,
            close: "Cancel",
        }
        setup() {
            super.setup();
            this.pos = usePos();
            this.orm = useService("orm");
            this.is_session = useRef("isSession")
            this.date_section = useRef("dateSection")
            this.dialog = useService("dialog");
            this.state = useState({
                current_session: false,
                start_date: "",
                end_date: ""
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
            // Get product summary
            var is_session = this.state.current_session;
            var start_date = this.state.start_date || '';
            var end_date = this.state.end_date || '';
            var order = this.pos.getOrder()['sequence_number']
            var domain = []
            if(is_session){
                domain = [['session_id', '=', this.pos.config.current_session_id.id]]
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
            }
                var orders = await this.orm.call('pos.order', 'search', [domain],);
                var order_ids = []
                orders.forEach(function(value, index) {
                       order_ids.push(value);
                });
                var products = await this.orm.call('pos.order', 'get_product_summary', [order, order_ids]);
                if (products.length != 0){
                    const { confirmed } = await this.dialog.add(ProductSummaryReceiptScreen,
                        {products: products, start_date: start_date, end_date: end_date, data: this.pos}
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
