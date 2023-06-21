/** @odoo-module **/
import PosComponent from 'point_of_sale.PosComponent';
import { mount } from "@odoo/owl";
import Registries from 'point_of_sale.Registries';
import { PosMsgView } from "./pos_msg_view"
class PosSystray extends PosComponent {
    setup(){
        super.setup(...arguments);
    }
    /** for opening the chat list window while click on the systray button*/
    onClick(ev) {
        if($(".pos_systray_template").length == 0){
            this.schedule_dropdown = mount(PosMsgView, document.body)
        }else if($(".pos_systray_template").length > 0){
            this.schedule_dropdown.then(function(res){
                res.__owl__.remove()
            })
        }
    }
}
PosSystray.template = 'PosSystray';
Registries.Component.add(PosSystray);
return PosSystray;
