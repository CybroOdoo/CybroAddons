/** @odoo-module */
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _lt } from '@web/core/l10n/translation';
/**
 * CustomAlertPopup component for displaying custom messages as an alert popup.
 * Inherits from AbstractAwaitablePopup.
 */
export class LaundryServiceTypePopup extends AbstractAwaitablePopup {
    // Create a new Popup instance
    laundryPopup(event) {
        var order = this.props.pos.get_order();
        if (order.selected_orderline && !this.props.orderline) {
            order.selected_orderline.set_washingType(this.props.pos.washing_type.find(obj => obj['id'] === parseInt(event.currentTarget.dataset['id'])));
        } else if (order.selected_orderline && this.props.orderline) {
            order.selected_orderline.set_washingType(this.props.pos.washing_type.find(obj => obj['id'] === parseInt(event.currentTarget.dataset['id'])));
        }
         super.confirm();
    }
}
LaundryServiceTypePopup.template = 'LaundryServiceTypePopup'
LaundryServiceTypePopup.defaultProps = {
    confirmText: _lt('Ok'),
    closePopup: _lt("Cancel"),
}
