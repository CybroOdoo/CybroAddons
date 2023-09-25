odoo.define('salesperson_pos_order_line.Order', function(require) {
    'use strict';
    // Import dependencies
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { useRef } = owl.hooks;
    var core = require('web.core');
    const {
        Gui
    } = require('point_of_sale.Gui');
    var _t = core._t;

    // Define the CustomDemoPopup class as a subclass of AbstractAwaitablePopup
    class CustomDemoPopup extends AbstractAwaitablePopup {

        constructor() {
            super(...arguments);
            this.salePersonRef = useRef('salePersonRef');
        }

        /**
         * Confirm the selected salesperson for the orderline.
         * If no orderline is selected, show an error popup.
         */
        confirm() {
            if (this.env.pos.get_order().get_selected_orderline()) {
                var order = this.env.pos.get_order().get_selected_orderline();
                var product_id = order.product.id;
                var product = this.env.pos.db.get_product_by_id(product_id);
                let option = this.salePersonRef.el.selectedOptions[0]
                order.set_salesperson([(option.value)]);
                this.trigger('close-popup');
            } else {
                Gui.showPopup("ErrorPopup", {
                    'title': _t("Error"),
                    'body': _.str.sprintf(_t('You should add product first')),
                });
                return false;
            }
        }
        /**
         * Close the popup without making any changes.
         */
        click_cancel(){
            this.trigger('close-popup');
        }
    }

    // Define the template for the CustomDemoPopup
    CustomDemoPopup.template = "CustomDemoPopup";

    // Register the CustomDemoPopup component with the point of sale Registries
    Registries.Component.add(CustomDemoPopup);

    // Export the CustomDemoPopup class for use in other modules
    return CustomDemoPopup
});
