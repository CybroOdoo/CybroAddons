/** @odoo-module **/
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { LocationSummaryPopup } from "./LocationPopup";

export class LocationSummaryButton extends Component {
// Extending Component and Adding Class LocationSummaryButton
    static template = "LocationSummaryButton";
        setup() {
            super.setup();
            this.pos = usePos();
            this.orm = useService("orm");
        }
        async onClick() {
            // Function to get all the location through rpc
            var locations = await this.orm.call('stock.location','search_read', [[['usage', '=', 'internal']]]);
            const { confirmed } = await this.pos.popup.add(LocationSummaryPopup,
                        { title: 'Location Summary',
                        locations: locations}
                      );
        }
    }
ProductScreen.addControlButton({
    component: LocationSummaryButton,
    condition: function () {
        return true;
    },
});
