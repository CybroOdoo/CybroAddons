/** @odoo-module */

import AbstractAwaitablePopup from 'point_of_sale.AbstractAwaitablePopup';
import Registries from 'point_of_sale.Registries';
import PosComponent from 'point_of_sale.PosComponent';
import { useListener } from '@web/core/utils/hooks';

// Extending the AbstractAwaitablePopup that used to add a new popup
class LaundryServiceTypePopup extends AbstractAwaitablePopup {
    setup() {
        super.setup();
    }
    // Create a new Popup instance
    laundryPopup(event) {
        var order = this.props.pos.get_order();
        if (order.selected_orderline && !this.props.orderline) {
            order.selected_orderline.set_washingType(this.env.pos.washing_type.find(obj => obj['id'] === parseInt(event.currentTarget.dataset['id'])));
        } else if (order.selected_orderline && this.props.orderline) {
            this.props.orderline.set_washingType(this.env.pos.washing_type.find(obj => obj['id'] === parseInt(event.currentTarget.dataset['id'])));
        }
        this.env.posbus.trigger('close-popup', {
            popupId: this.props.id,
            response: { confirmed: false, payload: null },
        });
    }
}
// Create Service popup
LaundryServiceTypePopup.template = 'LaundryServiceTypePopup';
LaundryServiceTypePopup.defaultProps = {
    confirmText: 'Ok',
    cancelText: 'Cancel',
};
Registries.Component.add(LaundryServiceTypePopup);
export default LaundryServiceTypePopup;
