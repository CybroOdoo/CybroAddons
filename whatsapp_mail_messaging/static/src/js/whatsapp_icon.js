/** @odoo-module **/
import { Dropdown } from '@web/core/dropdown/dropdown';
import { DropdownItem } from '@web/core/dropdown/dropdown_item';
import { registry } from '@web/core/registry';
import { Component } from '@odoo/owl';
/* Export new class WhatsappIcon by extending Component */
export class WhatsappIcon extends Component {
    /* On clicking whatsapp icon */
    async onclick_whatsapp_icon() {
        this.env.services['action'].doAction({
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
WhatsappIcon.components = { Dropdown, DropdownItem };
export const whatsapp_icon = {
    Component: WhatsappIcon,
};
registry.category('systray').add('WhatsappIcon', whatsapp_icon);
