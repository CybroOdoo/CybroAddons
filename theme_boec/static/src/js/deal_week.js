/** @odoo-module **/

import { registry } from "@web/core/registry";
import { renderToElement } from "@web/core/utils/render";
import { Interaction } from "@web/public/interaction";
import { rpc } from "@web/core/network/rpc";

export class DealWeek extends Interaction {
    static selector = ".deal_week_snippet_class";

    async willStart() {
        this.products = await this.waitFor(rpc("/get_products", {}));
        if (this.products) {
            this.countdown = await this.waitFor(rpc("/get_countdown", {}));
        }
    }

    start() {
        if (!this.products) {
            return;
        }
        this.removeChildren(this.el);
        this.insert(renderToElement("theme_boec.deal_week", { product_id: this.products }));
        const countdownEl = this.el.querySelector("#countdown");
        const endDate = this.countdown ? new Date(this.countdown).getTime() : NaN;
        if (!countdownEl || !Number.isFinite(endDate)) {
            return;
        }
        const updateCountdown = () => {
            const remaining = Math.max(0, Math.floor((endDate - Date.now()) / 1000));
            const values = [
                ["days", "Days", Math.floor(remaining / 86400)],
                ["hours", "Hours", Math.floor((remaining % 86400) / 3600)],
                ["minutes", "Minutes", Math.floor((remaining % 3600) / 60)],
                ["seconds", "Seconds", remaining % 60],
            ];
            countdownEl.innerHTML = values.map(([className, label, value]) =>
                `<span class="${className}">${value} <label>${label}</label></span>`
            ).join(" ");
        };
        updateCountdown();
        this.setSafeInterval(updateCountdown, 1000);
    }
}

registry.category("public.interactions").add("theme_boec.deal_week", DealWeek);
