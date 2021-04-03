odoo.define('pos_product_creation.product_create_popup', function(require) {
    'use strict';

    const {
        useState,
        useRef
    } = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    class ProductCreatePopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            console.log(this.env.pos, '<<<<<<<<<<<<<<<')
            this.state = useState({
                typeValue: this.props.startingValue,
                productValue: this.props.startingValue,
                priceValue: this.props.priceValue,
                productRef: this.props.startingValue
            });
        }
        getPayload() {
            var selected_vals = [];
            var category = this.state.typeValue;
            var product = this.state.productValue;
            var product_reference = this.state.productRef;
            var price = this.state.priceValue;
            var unit = this.state.unitValue;
            var product_category = this.state.categoryValue;
            selected_vals.push(category);
            selected_vals.push(product);
            selected_vals.push(product_reference);
            selected_vals.push(price);
            selected_vals.push(unit);
            selected_vals.push(product_category);
            return selected_vals
        }
    }
    ProductCreatePopup.template = 'ProductCreatePopup';
    ProductCreatePopup.defaultProps = {
        confirmText: 'Ok',
        cancelText: 'Cancel',
        array: [],
        title: 'Create ?',
        body: '',
        startingValue: '',
        priceValue: 1,
        list: [],
    };

    Registries.Component.add(ProductCreatePopup);

    return ProductCreatePopup;
});