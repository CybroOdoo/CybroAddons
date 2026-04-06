/** @odoo-module **/
import { Dropdown } from '@web/core/dropdown/dropdown';
import { DropdownItem } from '@web/core/dropdown/dropdown_item';
import { registry } from '@web/core/registry';
import { Component } from '@odoo/owl';
import { useService } from "@web/core/utils/hooks";
/* Export new class MailButton by extending Component */
export class MailButton extends Component {
    setup() {
        super.setup();
        this.action = useService("action");
    }
    /* On clicking mail icon */
    async onclick_mail_icon() {
        this.action.doAction({
            name: "Compose Mail",
            type: "ir.actions.act_window",
            res_model: 'message.mail.composer',
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
