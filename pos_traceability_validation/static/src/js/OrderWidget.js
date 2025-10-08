odoo.define('pos_traceability_validation.PoSOrderWidget', function (require) {
    'use strict';
    const OrderWidget = require('point_of_sale.OrderWidget');
    const Registries = require('point_of_sale.Registries');
    /**
     * Extends OrderWidget for passing the product IDs to the EditListPopup
     * validation
     */
    const PoSOrderWidget = (OrderWidget) =>
        class extends OrderWidget {
            async _editPackLotLines(event) {
                const orderline = event.detail.orderline;
                const isAllowOnlyOneLot = orderline.product.isAllowOnlyOneLot();
                const packLotLinesToEdit = orderline.getPackLotLinesToEdit(isAllowOnlyOneLot);
                const { confirmed, payload } = await this.showPopup('EditListPopup', {
                    title: this.env._t('Lot/Serial Number(s) Required'),
                    isSingleItem: isAllowOnlyOneLot,
                    array: packLotLinesToEdit,
                    product: orderline.product.id
                });
                if (confirmed) {
                    // Segregate the old and new packlot lines
                    const modifiedPackLotLines = Object.fromEntries(
                        payload.newArray.filter(item => item.id).map(item => [item.id, item.text])
                    );
                    const newPackLotLines = payload.newArray
                        .filter(item => !item.id)
                        .map(item => ({ lot_name: item.text }));

                    orderline.setPackLotLines({ modifiedPackLotLines, newPackLotLines });
                }
                this.order.select_orderline(event.detail.orderline);
            }
        }
    Registries.Component.extend(OrderWidget, PoSOrderWidget);
    return OrderWidget;
});
