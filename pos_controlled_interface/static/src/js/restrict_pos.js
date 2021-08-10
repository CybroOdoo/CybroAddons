odoo.define('pos_controlled_interface', function(require){
    "use strict";
const components = {
    NumpadWidget: require('point_of_sale.NumpadWidget'),
};
const { patch } = require('web.utils');

patch(components.NumpadWidget, 'pos_controlled_interface', {
        mounted() {
        console.log(this);

            if (this.env.pos.config.control_discount) {
                $($('.numpad').find('.mode-button')[2]).removeClass('disable');
            }else{
                $($('.numpad').find('.mode-button')[2]).addClass('disable');
            }
            if (this.env.pos.config.control_price) {
                $($('.numpad').find('.mode-button')[1]).removeClass('disable');
            }else{
                $($('.numpad').find('.mode-button')[1]).addClass('disable');
            }
        },
        changeMode(mode) {
            if (mode === 'discount'  && this.env.pos.config.control_discount) {
                return;
            }
            if (mode === 'price'  && this.env.pos.config.control_price) {
                return;
            }
            this.trigger('set-numpad-mode', { mode });
        }
});
});