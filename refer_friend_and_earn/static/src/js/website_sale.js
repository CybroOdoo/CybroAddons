import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

/**
 * Handles website interaction for toggling the referral points entry form in checkout/cart.
 */
export class ReferAndEarn extends Interaction {
    static selector = ".oe_website_sale, .o_cart_total, .wrap";
    dynamicContent = {
        ".show_points": {
            "t-on-click.prevent": this._onClickShowPoints,
        },
    };

    constructor(el, env = {}, metadata = {}) {
        super(el, env?.services ? env : { ...env, services: {} }, metadata);
    }

    /**
     * Shows the points form and hides the toggle link when clicked.
     */
    _onClickShowPoints(ev) {
        const link = ev?.currentTarget;
        if (!link) {
            return;
        }
        link.classList.add("d-none");
        const form = link.parentElement?.querySelector(".point_form") || document.querySelector(".point_form");
        if (form) {
            form.classList.remove("d-none");
        }
    }
}

registry.category("public.interactions").add("refer_friend_and_earn.refer_and_earn", ReferAndEarn);
