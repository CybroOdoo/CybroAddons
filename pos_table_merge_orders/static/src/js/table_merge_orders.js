odoo.define('pos_table_merge_orders.PosTableButton', function(require) {
    "use strict";
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');
    // Extends PosComponents and added a click function
    class PosTableButton extends PosComponent {
        setup() {
            super.setup();
            useListener('click', this.onClick);
        }
        async onClick(ev) {
            let self = this;
            this.showPopup('PosTablePopup');
            }
        }
    // It Shows the PosTableButton when enables the Allow Merge Table Orders field
    PosTableButton.template = 'PosTableButton';
    ProductScreen.addControlButton({
        component: PosTableButton,
        condition: function() {
            return this.env.pos.config.allow_merge_tables;
        },
    });
    Registries.Component.add(PosTableButton);
    return PosTableButton;
});
