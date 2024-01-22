/**@odoo-module **/
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
let img = "";
let base64_img = "";
/**
 * CreateProductPopup is a popup component for creating a new product in the Point of Sale.
 */
export class CreateProductPopup extends AbstractAwaitablePopup {
    static template = "CreateProductPopup"
    /**
     * Setup function to initialize the component.
     */
    setup() {
        super.setup();
        this.notification = useService("pos_notification");
        this.popup = useService("popup");
    }
    /**
     * Event handler for changing the image field.
     * @param {Event} ev - The event object.
     */
    async _onChangeImgField(ev) {
        try {
            let current = ev.target.files[0];
            const reader = new FileReader();
            reader.readAsDataURL(current);
            reader.onload = await
            function() {
                img = reader.result;
                base64_img = reader.result.toString().replace(/^data:(.*,)?/, "");
                const myTimeout = setTimeout(() => {
                    $("#img_url_tag_create").hide();
                    let element =
                        "<img src=" + img + " style='max-width: 150px;max-height: 150px;'/>";
                    $(".product-img-create-popup").append($(element));
                }, 100);
            };
            reader.onerror = (error) =>
                reject(() => {
                    throw error;
                });
        } catch (error) {
            throw error;
        }
    }
    /**
     * Confirm function to create the product based on the entered details.
     * @param {Event} ev - The event object.
     */
    async confirm(ev) {
        const img = $("#img_field").val();
        const name = $("#display_name").val();
        const price = $("#list_price").val()
        const cost = $("#cost_price").val();
        const category = $("#product_category").val();
        const barcode = $("#barcode").val();
        const default_code = $("#default_code").val();
        const type = $("#type").val();
        const values = {};
        if (base64_img) {
            values["image_1920"] = base64_img;
        }
        if (!name) {
            this.popup.add(ErrorPopup, {
                title: "Error",
                body: "Add product name",
            });
            return; // Stop execution if name is missing
        }
        values["name"] = name;
        if (cost) {
            values["standard_price"] = cost;
        }
        if (price) {
            values["lst_price"] = price;
        }
        if (category > 0) {
            values["pos_categ_ids"] = [[6, false, [category]]];
        } else {
            this.popup.add(ErrorPopup, {
                title: "Error",
                body: "Forgot to select pos category?",
            });
            return; // Stop execution if category is missing
        }
        if (barcode) {
            values["barcode"] = barcode;
        }
        if (default_code) {
            values["default_code"] = default_code;
        }
        if (type) {
            values["type"] = type;
        }
        values["available_in_pos"] = true;
        try {
        const result = await jsonrpc(`/web/dataset/call_kw/product.product/create`, {
                model: "product.product",
                method: "create",
                args: [values],
                kwargs: {},
            });
            if (result) {
                this.notification.add(_t("Product Created."), 3000);
                this.cancel()

            } else {
                this.notification.add(_t("Product Not Created."), 3000);
            }
        } catch (error) {
            throw error;
        }
    }
}