/** @odoo-module **/

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component } from "@odoo/owl";

export class InvoicingButton extends Component {
    static template = "pos_invoice_payment.InvoicingButton";

    setup() {
        super.setup();
        this.pos = usePos();
    }

    async onClick() {
        const result = await this.env.services.orm.call(
            'account.move',
            'get_invoices',
            []
        );
        this.pos.showScreen('InvoicingScreen', {
            invoices: result,
        });
    }
}

ProductScreen.addControlButton({
    component: InvoicingButton,
    condition: function () {
        return true;
    },
});
