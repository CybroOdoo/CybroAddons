/** @odoo-module **/
import { Component } from "@odoo/owl";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { InvoicingScreen } from "./invoicing_screen";
import { rpc } from "@web/core/network/rpc";
import { ConfirmationDialog, AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { onMounted, useState, mount } from "@odoo/owl";


patch(ControlButtons.prototype, {
    setup() {
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

    async GetInvoices() {
        try {
            const invoices = await this.orm.call("account.move", "get_invoices", []);
            if (this.state) {
                this.state.invoices = invoices;
            }
        } catch (error) {
            // Silence "Component is destroyed" error
            if (error?.message?.includes("destroyed")) {
                return;
            }
            throw error;
        }
    },

    async onClick() {
        // Show category summary popup
        if (this.state.invoices.length != 0) {
            this.dialog.add(InvoicingScreen, {
                title: "Invoices",
                invoices: this.state.invoices,
                fetchData: () => this.GetInvoices(),
            });
        }
    },
});

