/** @odoo-module **/
import { registry } from '@web/core/registry';
import { Component } from '@odoo/owl';
import { useService } from "@web/core/utils/hooks";

/* Export new class WhatsappIcon by extending Component */
export class WhatsappIcon extends Component {
    setup() {
        super.setup();
        this.action = useService("action");
    }
    /* On clicking whatsapp icon */
    async onclick_whatsapp_icon() {
        this.action.doAction({
            name: "Compose Whatsapp Message",
            type: "ir.actions.act_window",
            res_model: 'whatsapp.send.message',
            views: [[false, "form"]],
            view_mode: "form",
            target: "new",
        });
    }
}
WhatsappIcon.template = 'whatsapp_mail_messaging.whatsapp_icon';
WhatsappIcon.components = {};
export const whatsapp_icon = {
    Component: WhatsappIcon,
};
registry.category('systray').add('WhatsappIcon', whatsapp_icon, { sequence: 25 });
