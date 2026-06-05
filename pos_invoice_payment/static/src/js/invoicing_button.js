/** @odoo-module **/
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { InvoicingScreen } from "./invoicing_screen";
import { onMounted, useState } from "@odoo/owl";


patch(ControlButtons.prototype, {
    async setup() {
        super.setup();
        this.pos = usePos();
        this.dialog = useService("dialog");
        this.orm = useService("orm");
        this.state = useState({
            invoices: [],
        });
        onMounted(() => {
            this.GetInvoices();
        });


    },

    async GetInvoices(){
        this.state.invoices = await this.orm.call("account.move", "get_invoices",  []);

    },

    async onClick() {
    // Show category summary popup
        await this.GetInvoices();
        if (this.props.close) {
            this.props.close();
        }
        this.dialog.add(InvoicingScreen, {
            invoices: this.state.invoices || [],
        });
    },
});
