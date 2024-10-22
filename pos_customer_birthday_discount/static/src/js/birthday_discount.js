/** @odoo-module */
import { ActionpadWidget } from "@point_of_sale/app/screens/product_screen/action_pad/action_pad";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(ActionpadWidget.prototype, {

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

                var orderLines = self.pos.selectedOrder.orderlines;


                // Extract day and month from the partner's birthdate
                if (this.props.partner.birthdate) {
                    const birthDate = new Date(this.props.partner.birthdate);
                    const birthMonth = birthDate.getMonth() + 1;
                    const birthDay = birthDate.getDate();

                    // Compare day and month (ignore year)
                    if (birthDay === todayDay && birthMonth === todayMonth) {
                        isBirthday = true;

                        // If it's the partner's birthday, proceed to apply discount
                        this.props.partner['birthday'] = 'True';
                        this.first_order = self.pos.config.first_order;

                        // Call the backend method to check if it's the first order
                        this.check_pos_order().then(() => {
                            for (var order_id = 0; order_id < orderLines.length; order_id++) {
                                // Apply the discount
                                orderLines[order_id].set_discount(this.val);
                            }
                        });
                    } else {
                        // Reset discount if it's not the birthday
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
            // If the birthday is today and no order has been placed, set the discount
            this.val = Math.round(this.pos.config.discount * 100);
        }
    }
});
