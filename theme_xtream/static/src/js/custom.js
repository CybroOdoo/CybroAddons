/** @odoo-module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";

export class customXtream extends Interaction {
    static selector = "#wrapwrap";
    dynamicContent = {
        ".subscribe .input-group-append": { "t-on-click": this.onClickSubscribe },
        ".qtyplus": { "t-on-click.prevent": this.onClickIncrease },
        ".qtyminus": { "t-on-click.prevent": this.onClickDecrease },
    };

    onClickIncrease(ev) {
        this.changeQuantity(ev, 1);
    }

    onClickDecrease(ev) {
        this.changeQuantity(ev, -1);
    }

    changeQuantity(ev, delta) {
        const fieldName = ev.currentTarget.getAttribute("field");
        const inputs = [...this.el.querySelectorAll("input[name]")].filter(
            (input) => input.name === fieldName
        );
        const current = parseInt(inputs[0]?.value, 10);
        const quantity = Number.isNaN(current) ? 0 : Math.max(0, current + delta);
        for (const input of inputs) {
            input.value = quantity;
        }
    }

    async onClickSubscribe(ev) {
        const group = ev.currentTarget.parentElement;
        const button = ev.currentTarget.querySelector("span");
        const input = group.querySelector("input");
        const warning = group.parentElement.querySelector(".warning");
        if (!this.emailCheck(input.value)) {
            warning.textContent = _t("Enter a valid email.");
            warning.style.display = "";
            return;
        }
        if (button.dataset.subscribed || this.subscribing) {
            return;
        }
        this.subscribing = true;
        try {
            const subscribed = await this.waitFor(rpc("/subscribe_newsletter", {
                email: input.value,
            }));
            if (subscribed) {
                warning.style.display = "none";
                input.style.pointerEvents = "none";
                button.style.backgroundColor = "green";
                button.textContent = _t("THANKS");
                button.dataset.subscribed = "true";
            } else {
                warning.textContent = _t("Already subscribed to the newsletter.");
                warning.style.display = "";
            }
        } finally {
            this.subscribing = false;
        }
    }

    emailCheck(str) {
        return /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(str);
    }
}

registry.category("public.interactions").add("theme_xtream.custom", customXtream);
