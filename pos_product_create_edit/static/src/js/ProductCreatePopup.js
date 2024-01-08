odoo.define("pos_product_create_edit.ProductCreatePopup", function(require) {
    "use strict";

    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");
    const Registries = require("point_of_sale.Registries");
    const { isRpcError } = require('point_of_sale.utils');
    const { useListener } = require('web.custom_hooks');
    const { Gui } = require('point_of_sale.Gui');
    let img = "";
    let base64_img = "";
    class CreateProductPopup extends AbstractAwaitablePopup {
        setup() {
            super.setup();
            useListener("change", "#img_field", this._onChangeImgField.bind(this));
        }
        /**
         * Handles the change event of the image field.
         * Updates the selected image and displays it in the popup.
         * @param {Event} ev - The change event object.
         */
        async _onChangeImgField(ev) {
            try {
                let current = ev.target.files[0];
                const reader = new FileReader();
                reader.readAsDataURL(current);
                reader.onload = async function() {
                    img = reader.result;
                    base64_img = reader.result.toString().replace(/^data:(.*,)?/, "");
                    const myTimeout = setTimeout(() => {
                        $(ev.target.parentElement.previousElementSibling.childNodes[0]).hide();
                        let element =
                            "<img src=" + img + " style='max-width: 150px;max-height: 150px;'/>";
                        $(ev.target.parentElement.previousElementSibling.childNodes[0].parentElement).append($(element));
                    }, 100);
                };
                reader.onerror = function(error) {
                    console.log(error);
                };
            } catch (error) {
                if (isRpcError(error) && error.message.code < 0) {
                    Gui.showPopup('ErrorPopup', {
                        title: this.comp.env._t('Network Error'),
                        body: this.comp.env._t('Cannot access Product screen if offline.'),
                    });
                    Gui.setSyncStatus('error');
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
         * Confirms the creation of the product.
         * Sends a create request to the server with the entered product information.
         * Reloading the page after successful creation.
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
            }else{
                Gui.showPopup('ErrorPopup', {
                    title: this.env._t('Name Mandatory'),
                    body: this.env._t('Forgot to add name?'),
                });
                return false;
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
                    return false;
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
            try {
                const result = await this.rpc({
                    model: "product.product",
                    method: "create",
                    args: [values],
                });

                if (result) {
                    Gui.setSyncStatus(_.str.sprintf(this.env._t('%s - Product Created'), values["name"]), 3000);
                    window.location.reload();
                } else {
                    return False;
                }

                this.props.resolve({
                    confirmed: false,
                    payload: null
                });

                this.trigger('close-popup');
            } catch (error) {
                if (isRpcError(error) && error.message.code < 0) {
                    Gui.showPopup('ErrorPopup', {
                        title: this.comp.env._t('Network Error'),
                        body: this.comp.env._t('Cannot access Product screen if offline.'),
                    });
                    Gui.setSyncStatus('error');
                } else {
                    throw error;
                }
            }
        }
    }
    CreateProductPopup.template = "CreateProductPopup";
    Registries.Component.add(CreateProductPopup);
    return CreateProductPopup;
});
