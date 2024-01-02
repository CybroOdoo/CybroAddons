/** @odoo-module */
import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";

//Adding set_uom function to the props of Orderline
Orderline.props = {
    ...Orderline.props,
    line: {
        shape: {
            salesperson: { type: String, optional: true },
            user_id:{ type: Number, optional: true },
        }
    }
}
