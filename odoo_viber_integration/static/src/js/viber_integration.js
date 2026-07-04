/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onMounted , useRef, useState} from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

export class ViberSystray extends Component {
     /**
     * Setup the component.
     */
    setup() {
        super.setup(...arguments);
        this.viber_msg = useRef('viber_msg');
        this.user_select = useRef('user_select');
        onMounted(() => {
            this.viber_msg.el.hidden=true;
            var self = this;
            this.fetch_users()
        });
    }
   async fetch_users(){
     const result  = await rpc('/web/dataset/call_kw/res.users/get_users', {
                    model: 'res.users',
                    method: 'get_users',
                    args: [0],
                    kwargs: {}
                })
                 var select = this.user_select.el;

            // Create and append the default option
            var defaultOption = document.createElement('option');
            defaultOption.textContent = "Choose user to contact..";
            defaultOption.selected = true;  // Set as selected
            select.appendChild(defaultOption);

            // Create and append options for each user
            for (var i = 0; i < result.users.length; i++) {
                var option = document.createElement('option');
                option.value = result.users[i].phone;  // Set the value
                option.textContent = result.users[i].name;  // Set the text
                select.appendChild(option);
            }}
    OnCloseViber() {
       this.viber_msg.el.hidden=true;
    }
    /**
     * Show the Viber messaging form.
     */
    OnClickViber() {
        this.viber_msg.el.hidden=false;
    }
    /**
     * Action to perform when a user is selected.
     */
    onSelectionUser() {
        const select = this.user_select.el;
        if (select.value !== "Choose user to contact..") {
            const phone = select.value;
            const userNumber = phone.replace(/[-()\s]/g, ''); // Use regex to remove unwanted characters
            window.location.assign("viber://chat?number=" + userNumber);
        }
    }
}
ViberSystray.template = "ViberSystray";
export const systrayItem = {
    Component: ViberSystray,
};
registry.category("systray").add("ViberSystray", systrayItem, {
    sequence: 1
});
