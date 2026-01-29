/** @odoo-module **/
import PosComponent from 'point_of_sale.PosComponent';
import Registries from 'point_of_sale.Registries';
import { PosMsgView } from "./pos_msg_view";
import { MessagingMenu } from '@mail/components/messaging_menu/messaging_menu';
class PosSystray extends PosComponent {
    setup(){
        super.setup(...arguments);
        this.message_view = new MessagingMenu();
        this.MsgWindow = new PosMsgView();
    }
    /** for opening the chat list window while click on the systray button*/
    onClick(ev) {
        this.MsgWindow.toggle();
    }
}
PosSystray.template = 'PosSystray';
Registries.Component.add(PosSystray);
return PosSystray;
