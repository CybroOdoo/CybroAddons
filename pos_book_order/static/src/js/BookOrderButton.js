/** @odoo-module **/
/*
 * This file is used to register the a new button for booking orders with selected partner and products.
 */
import PosComponent from 'point_of_sale.PosComponent';
import Registries from 'point_of_sale.Registries';
import ProductScreen from 'point_of_sale.ProductScreen';

class BookOrderButton extends PosComponent {
    onClick() {
    // by clicking the booking order button, it will check whether at least one product and the selected customer or not, after that it will display popup.
        var order_lines = this.env.pos.get_order().orderlines;
        var partner = this.env.pos.get_order().get_partner()
        if (partner == null) {
            this.showPopup('ErrorPopup', {
                'title': "Please Select the Customer",
                'body': "You need to select a customer for using this option",
            });
        } else if (order_lines.length == 0) {
            this.showPopup('ErrorPopup', {
                'title': "Order line is empty",
                'body': "Please select at least one product",
            });
        } else {
            this.showPopup('BookOrderPopup', {
                partner: partner,
            });
        }
    }
}
BookOrderButton.template = 'BookOrderButton';
ProductScreen.addControlButton({
    component: BookOrderButton,
    condition: () => true,
});
Registries.Component.add(BookOrderButton);