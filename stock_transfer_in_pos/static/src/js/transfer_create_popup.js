/** @odoo-module **/
/**
     * This file is used register a popup for transferring the stock of selected products
     */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { TransferRefPopup } from "./transfer_ref_popup";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";



export class CreateTransferPopup extends AbstractAwaitablePopup {
    static template = "CreateTransferPopup";
    static defaultProps = {
        confirmText: _t("Save"),
        cancelText: _t("Discard"),
        clearText: _t("Clear"),
        title: "",
        body: "",
    };
       setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService("orm");
        this.dest_tr = useRef("dest_tr");
        this.source_tr = useRef("source_tr");
        this.picking = useRef("picking");
        this.source_loc = useRef("source_loc");
        this.dest_loc = useRef("dest_loc");
        this.stage = useRef("state");
    }
       _clickPicking(ev){
       // This hide and show destination and source location based on the picking type selected
           var type = ev.target.selectedOptions[0].dataset.type
           this.source_tr.el.classList.remove('d-none')
           this.dest_tr.el.classList.remove('d-none')
           if (type == 'incoming') {
               this.source_tr.el.classList.add('d-none')
           }
           else if (type == 'outgoing') {
              this.dest_tr.el.classList.add('d-none')
           }
       }
        async Create(){
        // This get all the values you selected in the popup and transfer the stock by passing data backend.
            var pick_id = this.picking.el.value;
            var source_id = this.source_loc.el.value;
            var dest_id = this.dest_loc.el.value;
            var state   = this.stage.el.value;
            var line = this.pos.get_order().orderlines;
            var product = {'pro_id':[],'qty':[]}
            if(pick_id){
                        for(var i=0; i<line.length;i++){
                 product['pro_id'].push(line[i].product.id)
                 product['qty'].push(line[i].quantity)
            }
            var self = this;
            await this.orm.call(
            "pos.config", "create_transfer", [pick_id,source_id,dest_id,state,product], {}
            ).then(function(result) {
            self.pos.popup.add(TransferRefPopup, {
            data: result
            });
            })
           this.cancel();
            }
            else{
                this.pos.popup.add(ErrorPopup, {
                title: _t("Select Picking Type"),
                body: _t(
                    "Please select a picking type for transferring"
                ),
            });
            }
        }
}
