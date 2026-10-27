/** @odoo-module */

import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { NumberPopup } from "@point_of_sale/app/components/popups/number_popup/number_popup";
import { reactive, onMounted, onWillUnmount } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";


patch(ControlButtons.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        // Inject the "Service Charge" tile into the "Actions" dialog.
        onMounted(() => this._injectServiceChargeTile());
        onWillUnmount(() => {
            if (this._serviceChargeTile) {
                this._serviceChargeTile.remove();
                this._serviceChargeTile = null;
            }
        });
    },

    /**
     * Add a "Service Charge" tile to the "Actions" dialog by cloning one of the
     * existing action tiles (Customer Note, Pricelist, Refund, ...), so it has
     * exactly the same markup, classes and size as them. The button is not
     * rendered in the main button row.
     */
    _injectServiceChargeTile(retry = true) {
        if (!this.showServiceChargeButton || this._serviceChargeTile) {
            return;
        }
        const bodies = document.querySelectorAll(".modal-body");
        const body = bodies[bodies.length - 1];
        // reference tile: a button that has sibling buttons (the actions grid)
        const buttons = body
            ? [...body.querySelectorAll("button")].filter(
                  (b) =>
                      !b.hasAttribute("data-service-charge-tile") &&
                      [...b.parentElement.children].filter((c) => c.tagName === "BUTTON").length > 1
              )
            : [];
        const ref = buttons[buttons.length - 1];
        if (!ref) {
            if (retry) {
                requestAnimationFrame(() => this._injectServiceChargeTile(false));
            }
            return;
        }
        const tile = ref.cloneNode(true);
        tile.setAttribute("data-service-charge-tile", "1");
        tile.removeAttribute("id");
        tile.removeAttribute("disabled");
        // icon
        const icon = tile.querySelector("i, svg, img");
        const newIcon = document.createElement("i");
        newIcon.className = "fa fa-fw fa-calculator";
        if (icon) {
            icon.replaceWith(newIcon);
        } else {
            tile.prepend(newIcon);
        }
        // label
        const walker = document.createTreeWalker(tile, NodeFilter.SHOW_TEXT);
        const textNodes = [];
        while (walker.nextNode()) {
            if (walker.currentNode.textContent.trim()) {
                textNodes.push(walker.currentNode);
            }
        }
        if (textNodes.length) {
            textNodes[0].textContent = _t("Service Charge");
            textNodes.slice(1).forEach((n) => (n.textContent = ""));
        } else {
            tile.append(document.createTextNode(_t("Service Charge")));
        }
        tile.addEventListener("click", () => this.onClickServiceChargeTile());
        ref.parentElement.appendChild(tile);
        this._serviceChargeTile = tile;
    },

    // Only offer the button inside the "Actions" dialog, not in the main row.
    get showServiceChargeButton() {
        return (
            !!this.pos.config.is_service_charges &&
            !!(this.props.showRemainingButtons || this.env.inDialog)
        );
    },

    onClickServiceChargeTile() {
        this.onClickServiceCharge();
        // close the "Actions" dialog like the other actions do
        if (this.props.close) {
            this.props.close();
        }
    },

    async onClickServiceCharge() {
        await this.dialog.add(NumberPopup, {
            title: _t("Service Charge"),
            startingValue: this.pos.config.service_charge,
            getPayload: (num) => {
                const val = Math.max(
                    0,
                    Math.min(100, this.env.utils.parseValidFloat(num.toString()))
                );
                if (val > 0) {
                    this.apply_service_charge(val);
                }
            },
        });
    },

    async apply_service_charge(val) {
        const order = this.pos.getOrder();
        const lines = order.getOrderlines();
        const product = this.pos.config.service_product_id;

        if (!product) {
            this.dialog.add(AlertDialog, {
                title: _t("Missing Product"),
                body: _t("Service product is not configured in POS settings."),
            });
            return;
        }
        // Remove the service charge line added earlier (if any)
        lines
            .filter((line) => line.product_id?.id === product.id)
            .forEach((line) => order.removeOrderline(line));

        // Calculate service charge amount
        const sc_price =
            this.pos.config.service_charge_type === "amount"
                ? val
                : (order.priceIncl * val) / 100;
        // Add service charge line
        await reactive(this.env.services.pos).addLineToCurrentOrder({
            product_tmpl_id: product.product_tmpl_id,
            price_unit: sc_price,
            taxes_id: []
        });
    },
});
