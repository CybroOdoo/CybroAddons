import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

/**
 * Saves the delivery date and the delivery slot chosen for a cart line.
 */
export class DeliverySlot extends Interaction {
    static selector = ".delivery_slot_div";
    dynamicContent = {
        "#slot_id": { "t-on-change": this.onSlotChange },
        "#date": { "t-on-change": this.onDateChange },
    };

    /**
     * Sends the chosen delivery slot to the server. When the server refuses
     * it (missing date, full slot, ...) a dialog is shown and the selection
     * is reset.
     *
     * @param {Event} ev
     */
    async onSlotChange(ev) {
        const select = ev.currentTarget;
        const deliverySlot = select.value;
        const lineId = select.dataset.lineId;
        if (!deliverySlot || !lineId) {
            return;
        }
        const response = await this.waitFor(
            rpc("/shop/cart/set_delivery_slot", {
                delivery_slot: deliverySlot,
                line_id: lineId,
            })
        );
        if (response.error) {
            let title = _t("Error");
            if (response.error_type === "limit_reached") {
                title = _t("Delivery Limit");
            } else if (response.error_type === "missing_date") {
                title = _t("Missing Delivery Date");
            }
            this.services.dialog.add(ConfirmationDialog, {
                title,
                body: response.error,
            });
            select.value = "";
        }
    }

    /**
     * Sends the chosen delivery date to the server.
     *
     * @param {Event} ev
     */
    async onDateChange(ev) {
        const deliveryDate = ev.currentTarget.value;
        const lineId = ev.currentTarget.dataset.lineId;
        if (!deliveryDate || !lineId) {
            return;
        }
        await this.waitFor(
            rpc("/shop/cart/set_delivery_date", {
                delivery_date: deliveryDate,
                line_id: lineId,
            })
        );
    }
}

registry
    .category("public.interactions")
    .add("delivery_slot.delivery_slot", DeliverySlot);
