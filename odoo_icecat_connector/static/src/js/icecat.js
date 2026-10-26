/** @odoo-module **/

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { loadJS } from "@web/core/assets";

export class IcecatProductInteraction extends Interaction {
    static selector = "#product_detail";

    dynamicContent = {
        _document: {
            "t-on-product_changed": (ev) => this.onProductChanged(ev),
        },
    };

    start() {
        this.fetchIcecatProductDetails();
    }

    onProductChanged(ev) {
        const newProductId = ev.detail?.productId;
        if (newProductId) {
            this.fetchIcecatProductDetails(newProductId);
        }
    }

    async renderIcecatLive(data) {
        if (typeof window.IcecatLive === "undefined" || !window.IcecatLive.getDatasheet) {
            try {
                await loadJS("https://live.icecat.biz/js/live-current-2.js");
            } catch {
                return;
            }
        }
        if (typeof window.IcecatLive !== "undefined" && window.IcecatLive.getDatasheet) {
            window.IcecatLive.getDatasheet({
                'title': '#icecat_title',
                'essentialinfo': '#icecat_essentialinfo',
                'marketingtext': '#icecat_marketingtext',
                'manuals': '#icecat_manuals',
                'reasonstobuy': '#icecat_reasonstobuy',
                'reviews': '#icecat_reviews',
                'featuregroups': '#icecat_featuregroups',
                'gallery': '#icecat_gallery',
                'featurelogos': '#icecat_featurelogos',
                'tours3d': '#icecat_tours3d',
                'videos': '#icecat_videos',
                'productstory': '#icecat_productstory'
            }, {
                Brand: data.brand,
                PartCode: data.product_code,
                UserName: data.username,
            }, 'en');
        }
    }

    fetchIcecatProductDetails(productId) {
        if (!productId) {
            const productBtn = this.el.querySelector('[data-action="add_to_cart"]') ||
                               this.el.querySelector('[data-product-id]');
            const productInput = this.el.querySelector('.product_id');
            productId = productBtn?.dataset?.productId || productInput?.value;
        }

        if (productId && parseInt(productId, 10)) {
            rpc('/get_icecat_product_details', {
                'product_id': parseInt(productId, 10),
            }).then((data) => {
                if (data && data.status) {
                    this.renderIcecatLive(data);
                }
            }).catch(() => {});
        }
    }
}

registry.category("public.interactions").add("odoo_icecat_connector.product_interaction", IcecatProductInteraction);
