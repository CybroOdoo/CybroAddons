/** @odoo-module **/
/*
 * This file is used to register the a new button to see booked orders data.
 */
import PosComponent from 'point_of_sale.PosComponent';
import Registries from 'point_of_sale.Registries';
import ProductScreen from 'point_of_sale.ProductScreen';
const rpc = require('web.rpc');

class BookedOrdersButton extends PosComponent {
    async onClick() {
    // Fetch all booked order in draft stage to screen
        var self = this
        await rpc.query({
            model: 'book.order',
            method: 'all_orders',
        }).then(function(result) {
            self.showScreen('BookedOrdersScreen', {
                data: result,
                new_order: false,
            });
        })
    }
}
BookedOrdersButton.template = 'BookedOrdersButton';
ProductScreen.addControlButton({
    component: BookedOrdersButton,
    condition: () => true
})
Registries.Component.add(BookedOrdersButton);