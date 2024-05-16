/**@odoo-module **/

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { registry } from "@web/core/registry";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";
import { getDataURLFromFile } from "@web/core/utils/urls";


export class CreateProductPopup extends AbstractAwaitablePopup {

     static defaultProps = {
        title: "",
        body: "",
        product: ""
    };

  setup() {
  super.setup();
        this.popup = useService("popup");
        this.pos = usePos();
        const product = this.props.product;
        this.changes = useState({
            name: product.display_name || "",
            image_1920: product.image_1920 || "",
            standard_price: product.standard_price || "",
            id: product.id || "",
            lst_price: product.lst_price || "",
            pos_categ_ids: product.pos_categ_ids || "",
            default_code: product.default_code || "",
            available_in_pos: true,
        });
    }

  async uploadImage(event) {
        const file = event.target.files[0];
        if (!file.type.match(/image.*/)) {
            await this.popup.add(ErrorPopup, {
                title: _t("Unsupported File Format"),
                body: _t("Only web-compatible Image formats such as .png or .jpeg are supported."),
            });
        } else {
            const imageUrl = await getDataURLFromFile(file);
            const loadedImage = await this._loadImage(imageUrl);
            if (loadedImage) {
                const resizedImage = await this._resizeImage(loadedImage, 800, 600);
                this.changes.image_1920 = resizedImage.toDataURL();
            }
        }
    }
    _resizeImage(img, maxwidth, maxheight) {
        var canvas = document.createElement("canvas");
        var ctx = canvas.getContext("2d");
        var ratio = 1;

        if (img.width > maxwidth) {
            ratio = maxwidth / img.width;
        }
        if (img.height * ratio > maxheight) {
            ratio = maxheight / img.height;
        }
        var width = Math.floor(img.width * ratio);
        var height = Math.floor(img.height * ratio);
        canvas.width = width;
        canvas.height = height;
        ctx.drawImage(img, 0, 0, width, height);
        return canvas;
    }
    get productImageUrl() {
        // We prioritize image_1920 in the `changes` field because we want
        // to show the uploaded image without fetching new data from the server.
        const product = this.props.product;
        if (this.changes.image_1920) {

            return this.changes.image_1920;
        } else if (product.id) {
            return `/web/image?model=product.product&id=${product.id}&field=image_1920&unique=${product.write_date}`;
        } else {
            return false;
        }
    }
    _loadImage(url) {
        return new Promise((resolve) => {
            const img = new Image();
            img.addEventListener("load", () => resolve(img));
            img.addEventListener("error", () => {
                this.popup.add(ErrorPopup, {
                    title: _t("Loading Image Error"),
                    body: _t("Encountered error when loading image. Please try again."),
                });
                resolve(false);
            });
            img.src = url;
        });
    }
        getPayload() {
             const processedChanges = {};
            for (const [key, value] of Object.entries(this.changes)) {
                    processedChanges[key] = value;
            }
            return processedChanges;
        }
}
CreateProductPopup.template = "CreateProductPopup";
