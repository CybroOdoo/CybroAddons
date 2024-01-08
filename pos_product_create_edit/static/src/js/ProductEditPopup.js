odoo.define("pos_product_create_edit.ProductEditPopup", function(require) {
    "use strict";
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");
    const Registries = require("point_of_sale.Registries");
    const { useListener } = require('web.custom_hooks');
    const { isRpcError } = require('point_of_sale.utils');
    const { Gui } = require('point_of_sale.Gui');
    let base64_img = "";
    let img = "";
    /**
     * EditProductPopup is a popup component used for editing product details in Odoo POS.
     */
    class EditProductPopup extends AbstractAwaitablePopup {
        setup() {
            super.setup();
            useListener("change", "#img_field", this._onChangeImgField.bind(this));
        }
        /**
         * Handle the change event of the image field.
         * @param {Event} ev - The change event.
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
                            "<img src=" +
                            img +
                            " style='max-width: 150px;max-height: 150px;'/>";
                        $(ev.target.parentElement.previousElementSibling.childNodes[0].parentElement).append($(element));
                    }, 100);
                };
                reader.onerror = function(error) {
                    console.log("error", error);
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
         * Confirm the changes made to the product.
         */
        async confirm(ev) {
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
            try {
                const result = await this.rpc({
                    model: "product.product",
                    method: "write",
                    args: [this.props.product.id, values],
                });
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
                        if (values["pos_categ_id"] == 0) {
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
                    this.showNotification(_.str.sprintf(this.env._t("%s - Product Update Failed"), values['name']), 3000);
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
        /**
         * Get the URL of the product image.
         * @returns {string} The URL of the product image.
         */
        get imageUrl() {
            const product = this.props.product;
            return `/web/image?model=product.product&field=image_128&id=${product.id}&unique=${product.write_date}`;
        }
    }
    EditProductPopup.template = "EditProductPopup";
    Registries.Component.add(EditProductPopup);
    return EditProductPopup;
});
