/** @odoo-module **/

import publicWidget from 'web.public.widget';
import ajax from 'web.ajax';
//Public Widget Class for Change subscription
publicWidget.registry.Change = publicWidget.Widget.extend({
    selector: '.change_sub_vehicle',
    start: function() {
        this._super.apply(this, arguments);
        this._onChangeCustomer(); // Call the function initially
    },
    //On the onchange function customer is passed to controller
    _onChangeCustomer: async  function(ev){
       var self=this;
       var customer_id = this.$('input[name="customer"]')[0].value
       await ajax.jsonRpc('/online/choose/vehicle', "call", {
                'customer_id': customer_id,
       })
       .then(function(result) {
            const select = self.$el.find('#change_vehicle_change')[0];
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
})
