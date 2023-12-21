/**@odoo-module **/
import AbstractAwaitablePopup from "point_of_sale.AbstractAwaitablePopup";
import Registries from "point_of_sale.Registries";
import { useListener } from "@web/core/utils/hooks";
const { Gui } = require('point_of_sale.Gui');
let base64_img = "";
let img = "";
class EditProductPopup extends AbstractAwaitablePopup {
    setup() {
        super.setup();
        useListener("change", "#img_field", this._onChangeImgField);
    }
    /**
     * Handle the change event of the image field.
     * @param {Event} ev - The change event object.
     */
    async _onChangeImgField(ev) {
        try {
            // This function will work when adding image to the image field
            var self = this;
            let current = ev.target.files[0];
            const reader = new FileReader();
            reader.readAsDataURL(current);
            reader.onload = await

            function() {
                img = reader.result;
                base64_img = reader.result.toString().replace(/^data:(.*,)?/, "");
                const myTimeout = setTimeout(() => {
                    $(ev.target.parentElement.previousElementSibling.childNodes[0]).hide();
                    let element =
                        "<img src=" +
                        img +
                        " style='max-width: 150px;max-height: 150px;'/>";
                    $(ev.target.parentElement.previousElementSibling.childNodes[0].parentElement).append($(element));
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
    /**
     * Function for validating number.
     */
    async _numberCheck(ev){
        ev.target.value = ev.target.value.replace(/[^0-9.]/g, '');
    }
    /**
     * Confirm the updates to the product.
     */
    confirm(ev) {
        let values = {};
        if (base64_img) {
            values["image_1920"] = base64_img;
        }
        if ($(ev.target.parentElement.parentElement.previousElementSibling.firstChild.firstElementChild.childNodes[3].childNodes[1]).val() != this.props.product.display_name) {
            values["name"] = $(ev.target.parentElement.parentElement.previousElementSibling.firstChild.firstElementChild.childNodes[3].childNodes[1]).val();
        }
        if ($(ev.target.parentElement.parentElement.previousElementSibling.firstChild.firstElementChild.childNodes[4].childNodes[1]).val() != this.props.product.list_price) {
            values["lst_price"] = $(ev.target.parentElement.parentElement.previousElementSibling.firstChild.firstElementChild.childNodes[4].childNodes[1]).val();
        }
        if ($(ev.target.parentElement.parentElement.previousElementSibling.firstChild.firstElementChild.childNodes[7].childNodes[1]).val()) {
            values["pos_categ_id"] = parseInt($(ev.target.parentElement.parentElement.previousElementSibling.firstChild.firstElementChild.childNodes[7].childNodes[1]).val());
        }
        if ($(ev.target.parentElement.parentElement.previousElementSibling.firstChild.firstElementChild.childNodes[6].childNodes[1]).val()) {
            values["barcode"] = $(ev.target.parentElement.parentElement.previousElementSibling.firstChild.firstElementChild.childNodes[6].childNodes[1]).val();
        }
        if ($(ev.target.parentElement.parentElement.previousElementSibling.firstChild.firstElementChild.childNodes[5].childNodes[1]).val()) {
            values["default_code"] = $(ev.target.parentElement.parentElement.previousElementSibling.firstChild.firstElementChild.childNodes[5].childNodes[1]).val();
        }
        if (values["pos_categ_id"] == 0) {
            Gui.showPopup('ErrorPopup', {
                title: this.env._t('Mismatch Category'),
                body: this.env._t('You cannot add to root category.'),
            });
        }
        this.rpc({
            model: "product.product",
            method: "write",
            args: [this.props.product.id, values],
        }).then((result) => {
            if (result) {
                if (values['name']) {
                    this.props.product.display_name = values['name'];
                }
                if (values['lst_price']) {
                    this.props.product.lst_price = values['lst_price'];
                }
                if (values['barcode']) {
                    this.props.product.lst_price = values['barcode'];
                }
                if (values['default_code']) {
                    this.props.product.lst_price = values['default_code'];
                }
                if (values['pos_categ_id']) {
                    if (values['pos_categ_id'] == 0) {
                        Gui.showPopup('ErrorPopup', {
                            title: this.env._t('Mismatch Category'),
                            body: this.env._t('You cannot add to root category.'),
                        });
                    } else {
                        this.props.product.pos_categ_id = [
                            values["pos_categ_id"],
                        ];
                    }
                }
                Gui.setSyncStatus(_.str.sprintf(this.env._t('%s - Product Created'), values['name']), 3000);
                window.location.reload();
            } else {
                this.showNotification(_.str.sprintf(this.env._t("%s - Product Updation Failed"), values['name']), 3000);
            }
            this.props.resolve({
                confirmed: false,
                payload: null
            });
            this.trigger('close-popup');
        });
    }
    /**
     * Get the URL for the product image.
     * @returns {string} The URL of the product image.
     */
    get imageUrl() {
        const product = this.props.product;
        return `/web/image?model=product.product&field=image_128&id=${product.id}&unique=${product.write_date}`;
    }
}
EditProductPopup.template = "EditProductPopup";
Registries.Component.add(EditProductPopup);
