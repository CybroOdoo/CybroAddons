/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { Checkout } from "@website_sale/interactions/checkout";
import { rpc } from "@web/core/network/rpc";

patch(Checkout.prototype, {
    async setup() {
        super.setup(...arguments);
        // Additional setup if needed
    },

    async _getCurrentLocation() {
        const data = await rpc("/shop/access_point/get");
        const carriers = this.el.querySelectorAll('.o_delivery_carrier_select');
        for (let carrier of carriers) {
            const radio = carrier.querySelector('input[type="radio"]');
            const deliveryType = radio.getAttribute("delivery_type");
            const deliveryName = carrier.querySelector('label').innerText;
            const showLoc = carrier.querySelector(".o_show_pickup_locations");
            if (!showLoc) {
                continue;
            }
            const orderLoc = carrier.querySelector(".o_order_location");
            if (data[deliveryType + '_access_point'] && data.delivery_name == deliveryName) {
                carrier.querySelector(".o_order_location_name").innerText = data.name;
                carrier.querySelector(".o_order_location_address").innerText = data[deliveryType + '_access_point'];
                orderLoc.parentElement.classList.remove('new-parent-class');
                showLoc.classList.add("d-none");
                break;
            } else {
                orderLoc.parentElement.classList.add("d-none");
                showLoc.classList.remove("d-none");
            }
        }
    },

    _showLoadingBadge(radio) {
        const deliveryPriceBadge = this._getDeliveryPriceBadge(radio);
        while (deliveryPriceBadge.firstChild) {
            deliveryPriceBadge.removeChild(deliveryPriceBadge.lastChild);
        }
        const loadingCircle = document.createElement('span');
        loadingCircle.classList.add("fa", "fa-circle-o-notch", "fa-spin");
        deliveryPriceBadge.appendChild(loadingCircle);
    },

    async _updateDeliveryMethod(radio) {
        await super._updateDeliveryMethod(...arguments);
        // Custom logic after delivery method update
        if (radio.checked) {
            // In Odoo 19, amount updates are handled in _updateCartSummaries(result)
            // which is called by the super._updateDeliveryMethod.
        }
    },
});
