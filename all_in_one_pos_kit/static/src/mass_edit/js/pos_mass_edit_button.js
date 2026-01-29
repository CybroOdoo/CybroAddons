odoo.define('pos_order_line_mass_edit.pos_mass_edit_button', function(require) {
    'use strict';
    const Registries = require('point_of_sale.Registries');
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require("@web/core/utils/hooks");

    class MassEditButton extends PosComponent {
        setup() {
            super.setup();
            useListener('click', this.onClick);
        }

        async onClick() {
            const order = this.env.pos.get_order();
            const orderLines = order.get_orderlines();
            if (!orderLines.length) {
                return this.showPopup('ErrorPopup', {
                    title: this.env._t('Order is Empty'),
                    body: this.env._t('You need to add product.'),
                });
            }

            const { confirmed } = await this.showPopup('MassEditPopup', {
                title: this.env._t('Edit Order Line'),
                body: orderLines.map(line => ({
                    id: line.id,
                    product: line.product,
                    quantity: line.quantity,
                    price: line.price,
                    discount: line.discount,
                })),
            });
        }
    }
    MassEditButton.template = 'MassEditButton';

    ProductScreen.addControlButton({
        component: MassEditButton,
        condition: function() {
            return this.env.pos;
        },
    });

    Registries.Component.add(MassEditButton);
    return MassEditButton;
});
