odoo.define('pos_magnify_image.MagnifyProductPopup', function (require) {
    "use strict";

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    class MagnifyProductPopup extends AbstractAwaitablePopup {
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
    Registries.Component.add(MagnifyProductPopup);
    return MagnifyProductPopup;
});