/** @odoo-module */

import AbstractAwaitablePopup from 'point_of_sale.AbstractAwaitablePopup';
import Registries from 'point_of_sale.Registries';
import PosComponent from 'point_of_sale.PosComponent';
import { useListener } from '@web/core/utils/hooks';
const {  useState, useRef } = owl;

// Extending the AbstractAwaitablePopup that used to add a new popup
class ProductCreatePopup extends AbstractAwaitablePopup {
    setup() {
        super.setup();
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
// Create Service popup
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
export default ProductCreatePopup;
