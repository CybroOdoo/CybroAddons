/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.Cancellation = publicWidget.Widget.extend({
    selector: '.cancel_sub',
    start: function () {
        this._super.apply(this, arguments);
        this._onChangeCustomer(); // Call the function initially
    },
    // On the onchange function customer is passed to controller
    _onChangeCustomer: async function (ev) {
        var self = this;
        var customerInput = this.$('input[name="customer"]')[0];
        if (!customerInput) {
            return;
        }
        var customer_id = customerInput.value;
        const result = await rpc('/online/choose/vehicle', {
            'customer_id': customer_id,
        });
        const select = self.$el.find('#vehicle_cancellation')[0];
        if (select) {
            const options = Array.from(select.options);
            options.forEach((option) => {
                option.remove();
            });
            result.forEach((item) => {
                let newOption = new Option(item[1], item[0]);
                select.add(newOption, undefined);
            });
        }
    }
});

