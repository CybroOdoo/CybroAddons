import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

/**
 * Filters the delivery slot dropdowns by Home Hours / Office Hours.
 */
export class SlotTime extends Interaction {
    static selector = ".slot-time-div";
    dynamicContent = {
        'input[type="radio"][name="slot_hour"]': {
            "t-on-change": this.onSlotTime,
        },
    };

    /**
     * Loads the slots of the selected type (`/shop/cart/get_option`) and
     * replaces the options of every delivery slot <select> of the cart.
     *
     * @param {Event} ev - The change event of the radio button.
     */
    async onSlotTime(ev) {
        const result = await this.waitFor(
            rpc("/shop/cart/get_option", {
                selected_option: ev.currentTarget.value,
            })
        );
        const selects = document.querySelectorAll(
            'select#slot_id, select[name="slot_id"]'
        );
        for (const select of selects) {
            select.replaceChildren(
                new Option(_t("Select a slot"), ""),
                ...result.map(([id, name]) => new Option(name, id))
            );
            select.selectedIndex = 0;
        }
    }
}

registry
    .category("public.interactions")
    .add("delivery_slot.slot_time", SlotTime);
