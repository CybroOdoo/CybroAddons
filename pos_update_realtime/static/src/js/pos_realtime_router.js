/** @odoo-module */

import { PosRouter } from "@point_of_sale/app/services/pos_router_service";
import { patch } from "@web/core/utils/patch";

/**
 * Patch the PosRouter to fix the "invalid props: unknown key 'orderUuid'" error
 * on LoginScreen.
 *
 * Root cause: When navigate() is called with routeParams (e.g. { orderUuid }),
 * those params are forwarded into matchURL(props). Inside matchURL, the params
 * are merged into state.params. If no route matches (fallback to LoginScreen),
 * state.params still contains orderUuid — which LoginScreen does not declare,
 * causing Owl's prop validation to throw.
 *
 * Fix: When the router falls back to LoginScreen, reset state.params to {}
 * so no unexpected props land on LoginScreen.
 */
patch(PosRouter.prototype, {
    matchURL(props = {}) {
        super.matchURL(...arguments);
        // If we fell back to LoginScreen, clear any stale params (e.g. orderUuid)
        // that LoginScreen does not accept as props.
        if (this.state.current === "LoginScreen") {
            this.state.params = {};
        }
    },
});
