/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component } from "@odoo/owl";
import { useState } from "@odoo/owl";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

let base64_img = "";  // GLOBAL variable to store processed base64 image

/**
 * Dialog for creating a new product directly from the POS interface.
 */
export class CreateProductDialog extends Component {
    static template = "CreateProductPopup";
    static components = { Dialog };

    /**
     * Component setup: initialize state and services.
     */
    setup() {
        this.pos = usePos();
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this.state = useState({
            preview_image: null,
        });
    }

    /**
     * Handles user image upload and converts to base64 for Odoo.
     */
    async _onChangeImgField(ev) {
    const file = ev.target.files[0];
    if (!file) return;

    const reader = new FileReader();

        reader.onload = () => {
            this.state.preview_image = reader.result;
            base64_img = reader.result.replace(/^data:(.*,)?/, "");
        };

    reader.readAsDataURL(file);
}


    /**
     * Confirm product creation.
     */
    async confirm() {
        try {
            const name = document.querySelector("#display_name")?.value?.trim();
            const price = parseFloat(document.querySelector("#list_price")?.value) || 0;
            const cost = parseFloat(document.querySelector("#cost_price")?.value) || 0;
            const category = parseInt(document.querySelector("#product_category")?.value);
            const barcode = document.querySelector("#barcode")?.value?.trim();
            const default_code = document.querySelector("#default_code")?.value?.trim();
            const type = document.querySelector("#type")?.value?.trim();

            if (!name) {
                return this.dialog.add(AlertDialog, {
                    title: _t("Error"),
                    body: _t("Please enter a Product Name."),
                });
            }

            if (!category || category <= 0) {
                return this.dialog.add(AlertDialog, {
                    title: _t("Error"),
                    body: _t("Please select a valid POS Category."),
                });
            }

            const values = {
                name,
                available_in_pos: true,
            };

            if (base64_img) values["image_1920"] = base64_img;
            if (cost) values["standard_price"] = cost;
            if (price) values["list_price"] = price;   // FIXED FIELD NAME
            if (category) values["pos_categ_ids"] = [[6, false, [category]]];
            if (barcode) values["barcode"] = barcode;
            if (default_code) values["default_code"] = default_code;
            if (type) values["type"] = type;

            const result = await rpc("/web/dataset/call_kw/product.product/create", {
                model: "product.product",
                method: "create",
                args: [values],
                kwargs: {},
            });

            if (result) {
                this.notification.add(_t("Product created successfully."), 3000);
                this.props.close();
            } else {
                this.notification.add(_t("Product creation failed."), 3000);
            }
        } catch (error) {
            this.notification.add(_t("Unexpected error occurred."), 3000);
        }
    }

    cancel() {
        this.props.close();
    }
}
