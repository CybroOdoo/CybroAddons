/**@odoo-module **/
import AbstractAwaitablePopup from "point_of_sale.AbstractAwaitablePopup";
import Registries from "point_of_sale.Registries";
import { isConnectionError } from "point_of_sale.utils";
import {useListener} from "@web/core/utils/hooks";
const { Gui } = require('point_of_sale.Gui');
let img = "";
let base64_img = "";
class CreateProductPopup extends AbstractAwaitablePopup {
    /**
     * Set up the component and attach the change event listener to the image field.
     */
    setup() {
        super.setup();
        useListener("change", "#img_field", this._onChangeImgField);
    }
    /**
     * Handle the change event of the image field.
     * @param {Event} ev - The change event object.
     */
    async _onChangeImgField(ev) {
        // This function will work when adding image to the image field
        try {
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
                        "<img src=" + img + " style='max-width: 150px;max-height: 150px;'/>";
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
     * Confirm the creation of the product.
     */
    async confirm(ev) {
        let img = $(ev.target.parentElement.parentElement.previousElementSibling.firstChild.firstElementChild.childNodes[2].children[1]).val();
        let name = $(ev.target.parentElement.parentElement.previousElementSibling.firstChild.firstElementChild.childNodes[3].children[1]).val();
        let price = $(ev.target.parentElement.parentElement.previousElementSibling.firstChild.firstElementChild.childNodes[4].children[1]).val();
        let cost = $(ev.target.parentElement.parentElement.previousElementSibling.firstChild.firstElementChild.childNodes[5].children[1]).val();
        let category = $(ev.target.parentElement.parentElement.previousElementSibling.firstChild.firstElementChild.childNodes[8].children[1]).val();
        let barcode = $(ev.target.parentElement.parentElement.previousElementSibling.firstChild.firstElementChild.childNodes[6].children[1]).val();
        let default_code = $(ev.target.parentElement.parentElement.previousElementSibling.firstChild.firstElementChild.childNodes[7].children[1]).val();
        let values = {};
        if (base64_img) {
            values["image_1920"] = base64_img;
        }
        if (name) {
            values["name"] = name;
        }
        if (cost) {
            values["standard_price"] = cost;
        }
        if (price) {
            values["lst_price"] = price;
        }
        if (category) {
            if (category == 0){
                Gui.showPopup('ErrorPopup', {
                    title: this.env._t('Mismatch Category'),
                    body: this.env._t('You cannot add to root category.'),
                });
            }else{
                values["pos_categ_id"] = category;
            }
        }
        if (barcode) {
            values["barcode"] = barcode;
        }
        if (default_code) {
            values["default_code"] = default_code;
        }
        values["available_in_pos"] = true;
        await this.rpc({
            model: "product.product",
            method: "create",
            args: [values],
        }).then((result) => {
            if (result) {
                this.showNotification(_.str.sprintf(this.env._t('%s - Product Created'), values["name"]), 3000);
                window.location.reload();
            } else {
                this.showNotification(_.str.sprintf(this.env._t('%s - Product Creation Failed'), values["name"]), 3000);
            }
            this.props.resolve({
                confirmed: false,
                payload: null
            });
            this.trigger('close-popup');
        });
    }
}
CreateProductPopup.template = "CreateProductPopup";
Registries.Component.add(CreateProductPopup);
