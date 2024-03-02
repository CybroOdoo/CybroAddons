/** @odoo-module **/
import { Dropdown } from '@web/core/dropdown/dropdown';
import { DropdownItem } from '@web/core/dropdown/dropdown_item';
import { registry } from '@web/core/registry';
import { Component } from '@odoo/owl';
/* Export new class MailButton by extending Component */
export class MailButton extends Component {
    /* On clicking mail icon */
    async onclick_mail_icon() {
        this.env.services['action'].doAction({
            name: "Compose Mail",
            type: "ir.actions.act_window",
            res_model: 'mail.mail',
            views: [[false, "form"]],
            view_mode: "form",
            target: "new",
        });
    }
}
MailButton.template = 'whatsapp_mail_messaging.mail_icon';
MailButton.components = {Dropdown, DropdownItem};
export const mailbutton = {
    Component: MailButton,
};
registry.category('systray').add('MailButton', mailbutton);
