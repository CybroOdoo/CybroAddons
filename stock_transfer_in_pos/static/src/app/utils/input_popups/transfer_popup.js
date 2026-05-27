/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { Component, useRef} from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { WarningDialog } from "@web/core/errors/error_dialogs";
import { TransferRefPopup } from "@stock_transfer_in_pos/app/utils/input_popups/transfer_ref_popup";


export class TransferPopup extends Component {
    static template = "stock_transfer_in_pos.TransferPopup";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        data: {  type: Object, optional: true },
        confirmButtonLabel: { type: String, optional: true },
        close: Function,
    };
    static defaultProps = {
        title: _t("Confirm?"),
        confirmButtonLabel: "Confirm",
    };

    setup() {
        this.dialog = useService("dialog");
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
           //This will hide and show destination and source location based on
           //the picking type selected
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
    //Confirm button for create the transfer in backend
    async confirm(){
        // Retrieved all the values you selected in the popup and transfer the
        // stock by passing data to the backend.
            var pick_id = this.picking.el.value;
            var source_id = this.source_loc.el.value;
            var dest_id = this.dest_loc.el.value;
            var state   = this.stage.el.value;
            var line = this.pos.getOrder().lines;
            var product = {'pro_id':[],'qty':[]}
            if(pick_id ){
                 for(var i=0; i<line.length;i++){
                 product['pro_id'].push(line[i].product_id.id)
                 product['qty'].push(line[i].qty)
            }
            var self = this;
            await this.orm.call(
            "pos.config", "create_transfer", [pick_id,source_id,dest_id,state,product], {}
            ).then(function(result) {
            self.dialog.add(TransferRefPopup, {
                        title: _t("Success"),
                        data: result,
                    });
            })
           this.cancel();
            }
            else{
                this.dialog.add(WarningDialog, {
                        title: _t("Select Picking Type"),
                        message: _t("Please select a picking type for transferring"),
                    });
            }
        }

    cancel() {
        this.props.close();
    }
}