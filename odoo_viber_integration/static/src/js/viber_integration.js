/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onMounted } from "@odoo/owl";
import { jsonrpc } from "@web/core/network/rpc_service";

export class ViberSystray extends Component {
     /**
     * Setup the component.
     */
    setup() {
        super.setup(...arguments);
        onMounted(() => {
            $("#viber_msg_form").hide();
            var self = this;
            jsonrpc('/web/dataset/call_kw/res.users/get_users', {
                    model: 'res.users',
                    method: 'get_users',
                    args: [0],
                    kwargs: {}
                })
                .then(function result(e) {
                    var select = $('#user_select');
                    var option = $('<option>').attr('selected', 'selected').text("Choose user to contact..");
                    select.append(option);
                    for (var i = 0; i < e.users.length; i++) {
                        var option = $('<option>').val(e.users[i].phone);
                        option.text(e.users[i].name);
                        select.append(option);
                    }
                })
        });
    }
    OnCloseViber() {
        $("#viber_msg_form").hide();
    }
    /**
     * Show the Viber messaging form.
     */
    OnClickViber() {
        $("#viber_msg_form").show();
    }
    /**
     * Action to perform when a user is selected.
     */
    onSelectionUser() {
        if ($("#user_select").val() != "Choose user to contact..") {
            var phone = $("#user_select").val()
            var user_number = phone.replace('-', '').replace('(', "").replace(')', '').replace(' ', '')
            window.location.assign("viber://chat?number=" + user_number)
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
