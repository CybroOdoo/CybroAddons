//Extends the AbstractAwaitablePopup component in the Point of Sale to display a popup with a magnified image of a product.
odoo.define('all_in_one_pos_kit.MagnifyProductPopup', function(require) {
    "use strict";
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    class MagnifyProductPopup extends AbstractAwaitablePopup {
        //    Retrieves the URL for the large image of the product.
        constructor() {
            super(...arguments);
        }
        get largeImageUrl() {
            const product = this.props['body'];
            return `/web/image?model=product.product&field=image_1920&id=${product.id}&write_date=${product.write_date}&unique=1`;
        }
    }
    MagnifyProductPopup.template = 'MagnifyProductPopup';
    MagnifyProductPopup.defaultProps = {
        cancelText: 'Close',
    };
    MagnifyProductPopup.template = 'MagnifyProductPopup';
    // Register the component in the component registry
    Registries.Component.add(MagnifyProductPopup);
    return MagnifyProductPopup;
});
