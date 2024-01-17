/**@odoo-module **/
import AbstractAwaitablePopup from "point_of_sale.AbstractAwaitablePopup";
import Registries from "point_of_sale.Registries";
import { useListener } from "@web/core/utils/hooks";
let base64_img = "";
let img = "";
// A custom popup component for editing a product in the Point of Sale.
class EditProductPopup extends AbstractAwaitablePopup {
    setup() {//Sets up the component by registering the change event listener for the image field.
    super.setup();
    useListener("change", "#img_field", this._onChangeImgField);
    }
    //Handles the change event of the image field and updates the image preview. @param {Event} ev - The change event.
    async _onChangeImgField(ev) {
        try {
        // This function will work when adding image to the image field
            var self = this;
            let current = ev.target.files[0];
            const reader = new FileReader();
            reader.readAsDataURL(current);
            reader.onload = await function () {
                img = reader.result;
                base64_img = reader.result.toString().replace(/^data:(.*,)?/, "");
                const myTimeout = setTimeout(() => {
                let element =
                "<img src=" +
                img +
                " style='max-width: 150px;max-height: 150px;'/>";
                $(ev.srcElement.offsetParent).find('.product-img-create-popup').append($(element));
                }, 100);
            };
            reader.onerror = (error) =>
            reject(() => {
                console.log("error", error);
            });
        } catch (error) {
            if (isConnectionError(error)) {
            this.showPopup("ErrorPopup", {
            title: this.env._t("Network Error"),
            body: this.env._t("Cannot access Product screen if offline."),
            });
            } else {
                throw error;
            }
        }
    }
    confirm() {//Performs the product update based on the modified values and closes the popup.
        let values = {};
        if (base64_img) {
            values["image_1920"] = base64_img;
        }
        if ($(this.el).find("#display_name")[0].value != this.props.product.display_name) {
            values["name"] = $(this.el).find("#display_name")[0].value;
        }
        if ($(this.el).find("#list_price")[0].value != this.props.product.list_price) {
            values["lst_price"] = $(this.el).find("#list_price")[0].value;
        }
        if ($(this.el).find("#product_category")[0].value) {
            values["pos_categ_id"] = parseInt($(this.el).find("#product_category")[0].value);
        }
        if ($(this.el).find("#barcode")[0].value) {
            values["barcode"] = parseInt($(this.el).find("#barcode")[0].value);
        }
        if ($(this.el).find("#default_code")[0].value) {
            values["default_code"] = parseInt($(this.el).find("#default_code")[0].value);
        }
        this.rpc({
            model: "product.product",
            method: "write",
            args: [this.props.product.id, values],
        }).then((result) => {
            if (result) {
                this.props.product.display_name = $(this.el).find("#display_name")[0].value;
                this.props.product.lst_price = $(this.el).find("#list_price")[0].value;
                this.props.product.barcode = $(this.el).find("#barcode")[0].value;
                this.props.product.default_code = $(this.el).find("#default_code")[0].value;
                this.props.product.pos_categ_id = [
                parseInt($(this.el).find("#product_category")[0].value),
                $(this.el).find("#product_category")[0].selectedOptions[0].title,
                ];
                this.showNotification(_.str.sprintf(this.env._t("%s - Product Updated"),$(this.el).find("#display_name")[0].value),3000);
            } else {
                this.showNotification(_.str.sprintf(this.env._t("%s - Product Updation Failed"),$(this.el).find("#display_name")[0].value),3000);
            }
            this.env.posbus.trigger("close-popup", {
                popupId: this.props.id,
                response: {
                    confirmed: false,
                    payload: null,
                },
            });
        });
    }
    cancel() {//Cancels the editing and closes the popup.
        this.env.posbus.trigger("close-popup", {
            popupId: this.props.id,
            response: {
                confirmed: false,
                payload: null,
            },
        });
    }
    get imageUrl() {//Retrieves the URL of the product image. @returns {string} The URL of the product image.
        const product = this.props.product;
        return `/web/image?model=product.product&field=image_128&id=${product.id}&unique=${product.write_date}`;
    }
}
EditProductPopup.template = "EditProductPopup";
Registries.Component.add(EditProductPopup);
