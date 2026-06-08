/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { LaundryServiceTypePopup } from "@laundry_management_pos/js/popup/washing_type_popup";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";

patch(ControlButtons.prototype, {
    /**
     * Set up washing type loader — data is fetched once on mount
     * so that this.orm is ready and the component is live.
     */
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
        this.dialog = useService("dialog");
        this.orm = useService("orm");
        onMounted(() => this._loadWashingTypes());
    },

    /**
     * Fetch washing type records from the backend and store on pos.
     */
    async _loadWashingTypes() {
        try {
            const washingTypeData = await this.orm.call(
                "washing.type",
                "search_read",
                [],
                {
                    fields: ["name", "assigned_person_id", "amount", "id"],
                }
            );
            this.pos.washing_type = washingTypeData;
        } catch (error) {
            console.error("Failed to load washing types:", error);
        }
    },

    /**
     * Open the laundry service selection popup.
     */
    onWashingClick() {
        this.dialog.add(LaundryServiceTypePopup, {
            title: _t("Laundry Service"),
            body: _t("Choose the Washing type"),
            service: this.pos.washing_type,
            pos: this.pos,
            orderline: this.props.line,
        });
    },
});
