odoo.define('salesperson_pos_order_line.Order', function(require) {
    'use strict';
    /**
     * This module defines the CustomDemoPopup class, which is a custom popup component that allows the user to set the
     * salesperson for a selected order line.
     */
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { useRef } = owl.hooks;
    var core = require('web.core');
    const { Gui } = require('point_of_sale.Gui');
    var _t = core._t;
    class CustomDemoPopup extends AbstractAwaitablePopup {
        /**
         * Initializes the component.
         */
        constructor() {
            super(...arguments);
            this.salePersonRef = useRef('salePersonRef');
        }
        /**
         * Confirms the selected salesperson and sets it for the selected order line.
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
         * Cancels the popup.
         */
        click_cancel() {
            this.trigger('close-popup');
        }
    }
    CustomDemoPopup.template = "CustomDemoPopup";
    Registries.Component.add(CustomDemoPopup);
    return CustomDemoPopup
});
