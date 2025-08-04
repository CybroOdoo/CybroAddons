/** @odoo-module */
import { SelectPartnerButton } from "@point_of_sale/app/screens/product_screen/control_buttons/select_partner_button/select_partner_button";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(SelectPartnerButton.prototype, {
    setup() {
        super.setup();
        this.orm = useService('orm');
    },

    get isBirthDay() {
        this.val = 0;
        var self = this;
        var isBirthday = false;
        if (this.pos.config.birthday_discount) {
             if (this.props.partner) {
                    const systemDate = new Date();
                     // Extract day and month from the current system date
                     const todayMonth = systemDate.getMonth() + 1;  // months are zero-indexed, so January is 0
                     const todayDay = systemDate.getDate();
                     var orderLines = self.pos.selectedOrder.lines;
                     if (this.props.partner.birthdate) {
                     const birthDate = new Date(this.props.partner.birthdate);
                     const birthMonth = birthDate.getMonth() + 1;
                     const birthDay = birthDate.getDate();
                         if (birthDay === todayDay && birthMonth === todayMonth) {
                             isBirthday = true;
                             this.props.partner['birthday'] = 'True';
                             this.first_order = self.pos.config.first_order;
                             this.check_pos_order().then(() => {
                                   for (var order_id = 0; order_id < orderLines.length; order_id++) {
                                     orderLines[order_id].set_discount(this.val);
                                   }
                             });
                         }else {
                                for (var order_id = 0; order_id < orderLines.length; order_id++) {
                                     orderLines[order_id].set_discount(0);
                                }

                         }
                     } else {
                           for (var order_id = 0; order_id < orderLines.length; order_id++) {
                                    orderLines[order_id].set_discount(0);
                           }
                     }
             }
        }
        return isBirthday;
    },

    async check_pos_order() {
        // Call the Python method to check if it is the partner's birthday and if it's their first order
        const result = await this.orm.call("pos.config", "check_pos_order", [this.props.partner.id, this.first_order]);
        if (result['birthday'] == 'True' && result['order'] == 'False') {
            this.val = Math.round(this.pos.config.discount * 100);
        }
    }
});
