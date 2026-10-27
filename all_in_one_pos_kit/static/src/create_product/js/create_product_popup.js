/** @odoo-module */

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";

// Small popup used by the "Create Product" button of the product screen.
export class CreateProductPopup extends Component {
    static template = "all_in_one_pos_kit.CreateProductPopup";
    static components = { Dialog };
    static props = {
        categories: { type: Array },
        onConfirm: { type: Function },
        close: { type: Function },
    };

    setup() {
        this.state = useState({
            name: "",
            price: "",
            barcode: "",
            categId: "",
            error: "",
            saving: false,
        });
    }

    async confirm() {
        const name = this.state.name.trim();
        const price = parseFloat(this.state.price || "0");
        if (!name) {
            this.state.error = _t("Please enter a product name.");
            return;
        }
        if (isNaN(price) || price < 0) {
            this.state.error = _t("Please enter a valid price.");
            return;
        }
        this.state.error = "";
        this.state.saving = true;
        try {
            await this.props.onConfirm({
                name,
                price,
                barcode: this.state.barcode.trim(),
                categId: this.state.categId ? parseInt(this.state.categId) : false,
            });
            this.props.close();
        } catch (e) {
            this.state.saving = false;
            this.state.error =
                (e && e.data && e.data.message) || (e && e.message) || _t("The product could not be created.");
        }
    }
}
