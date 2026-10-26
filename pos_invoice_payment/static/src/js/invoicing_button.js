import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { InvoicingScreen } from "./invoicing_screen";

patch(ControlButtons.prototype, {
    setup() {
        super.setup();
        this.dialog = useService("dialog");
    },

    clickInvoicing() {
        this.dialog.add(InvoicingScreen, {
            title: "Invoices",
            invoices: [],
        });
    },
});
