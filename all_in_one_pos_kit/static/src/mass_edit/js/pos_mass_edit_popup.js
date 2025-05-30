/** @odoo-module **/
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";

export class MassEditPopup extends AbstractAwaitablePopup {
    static template = "MassEditPopup";
    static defaultProps = {
        confirm: "Confirm",
        cancel: "Cancel",
    };
    async confirm(){
//    function for confirm button inside popup
        window.location.reload();
    }
    sendInput(key) {
        for(var line in this.props.body) {
            if (this.props.body[line].id == key){
                this.props.body[line].quantity = 0
            }
        }
    }
}
