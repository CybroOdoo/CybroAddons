/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { jsonrpc } from "@web/core/network/rpc_service";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";
//Refund password validation and popup
patch(TicketScreen.prototype, {
 async onDoRefund() {
        var refund="";
            var session_refund= false;
            var data = await this.orm.call("pos.config", "fetch_global_refund_security", [])
            refund = data;
            if (!refund){
                session_refund = this.pos.config.refund_security;
                }
            if(refund){
                const { confirmed, payload } = await this.popup.add(NumberPopup, { isPassword: true })
                if(refund == payload){
                    super.onDoRefund(...arguments);
                }
                else{
                       this.popup.add(ErrorPopup,{
                        body : _t('Invalid Password, Enter your global password'),
                        });
                    }
            }
            else if(session_refund){
                const { confirmed, payload } = await this.popup.add(NumberPopup, { isPassword: true })
                if(session_refund == payload){
                    super.onDoRefund(...arguments);
                }
                else{
                        this.popup.add(ErrorPopup,{
                        body : _t('Incorrect Password'),
                        });
                    }
            }
            else{
                super.onDoRefund(...arguments);
            }
    },
        })
