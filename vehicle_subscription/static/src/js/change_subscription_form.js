/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.Change = publicWidget.Widget.extend({
    selector: '.change_sub_vehicle',
    start: function () {
        this._super.apply(this, arguments);
        this._onChangeCustomer(); // Call the function initially
    },
    //On the onchange function customer is passed to controller
    _onChangeCustomer: async function (ev) {
        var self = this;
        var customer_id = this.$('input[name="customer"]')[0].value
        await rpc('/online/choose/vehicle', {
            'customer_id': customer_id,
        })
            .then(function (result) {
                const select = self.$el.find('#vehicle_change')[0];
                const options = Array.from(select.options);
                options.forEach((option) => {
                    option.remove();
                });
                result.forEach((item) => {
                    let newOption = new Option(item[1], item[0]);
                    select.add(newOption, undefined);
                });
            });
    },
});
