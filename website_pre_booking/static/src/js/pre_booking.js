import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

function submitPreBooking(button) {
    if (!button) {
        return;
    }
    const targetUrl = button.dataset.url;
    if (!targetUrl) {
        return;
    }

    const productEl = button.closest(".js_product");
    const quantityInput = (productEl || document).querySelector('input[name="add_qty"]');
    const quantity = parseFloat(quantityInput?.value) || 1;
    const csrfToken = button.dataset.csrfToken;

    const form = document.createElement("form");
    form.method = "POST";
    form.action = targetUrl;

    if (csrfToken) {
        const csrfInput = document.createElement("input");
        csrfInput.type = "hidden";
        csrfInput.name = "csrf_token";
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
    }

    const qtyInput = document.createElement("input");
    qtyInput.type = "hidden";
    qtyInput.name = "prod_qty";
    qtyInput.value = quantity;
    form.appendChild(qtyInput);

    document.body.appendChild(form);
    form.submit();
}

export class WebsiteSalePrebooking extends Interaction {
    static selector = ".pre_booking";

    dynamicContent = {
        _root: {
            "t-on-click.prevent": this._preBooking,
        },
    };

    /**
     * Handles the pre-booking button click.
     *
     * @param {MouseEvent} ev
     */
    _preBooking(ev) {
        submitPreBooking(ev.currentTarget);
    }
}

registry
    .category("public.interactions")
    .add("website_sale.prebooking", WebsiteSalePrebooking);
