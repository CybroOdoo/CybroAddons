/** @odoo-module **/

import { Dialog } from "@web/core/dialog/dialog";
import { Component, useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

let img = "";
let base64_img = "";

export class CreateProductPopup extends Component {
    static template = "CreateProductPopup";
    static components = { Dialog };
    static props = {
        close: { type: Function, optional: true },
        getPayload: { type: Function, optional: true },
    };

    setup() {
        this.pos = usePos();
        this.notification = useService("notification");
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.state = useState({
            imageUrl: false,
        });
    }

    async _onChangeImgField(ev) {
        let current = ev.target.files[0];
        if (!current) return;
        const reader = new FileReader();
        reader.readAsDataURL(current);
        reader.onload = () => {
            img = reader.result;
            base64_img = reader.result.toString().replace(/^data:(.*,)?/, "");
            this.state.imageUrl = img;
        };
    }

    async confirm() {
        const name = document.getElementById("display_name")?.value;
        const price = document.getElementById("list_price")?.value;
        const cost = document.getElementById("cost_price")?.value;
        const category = document.getElementById("product_category")?.value;
        const barcode = document.getElementById("barcode")?.value;
        const default_code = document.getElementById("default_code")?.value;
        const type = document.getElementById("type")?.value;
        const values = {};

        if (base64_img) {
            values["image_1920"] = base64_img;
        }
        if (!name) {
            this.dialog.add(AlertDialog, {
                title: "Error",
                body: "Add product name",
            });
            return;
        }
        values["name"] = name;
        if (cost) values["standard_price"] = parseFloat(cost);
        if (price) values["lst_price"] = parseFloat(price);

        if (parseInt(category) > 0) {
            values["pos_categ_ids"] = [[6, false, [parseInt(category)]]];
        } else {
            this.dialog.add(AlertDialog, {
                title: "Error",
                body: "Forgot to select pos category?",
            });
            return;
        }
        if (barcode) values["barcode"] = barcode;
        if (barcode) values["barcode"] = barcode;
        if (default_code) values["default_code"] = default_code;
        
        if (type === 'product') {
            values["type"] = 'consu';
            values["is_storable"] = true;
        } else {
            if (type) values["type"] = type;
        }

        values["available_in_pos"] = true;
        values["sale_ok"] = true;

        try {
            const result = await this.orm.create("product.product", [values]);
            if (result) {
                this.notification.add("Product Created.", { type: "success" });
                this.props.close();
            } else {
                this.notification.add("Product Not Created.", { type: "danger" });
            }
        } catch (error) {
            console.error(error);
        }
    }

    cancel() {
        this.props.close();
    }
}