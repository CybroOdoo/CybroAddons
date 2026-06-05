/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { LaundryServiceTypePopup } from "@laundry_management_pos/js/popup/washing_type_popup";
import { patch } from "@web/core/utils/patch";

/**
 * Patch ControlButtons to load washing type data and handle clicks.
 */
patch(ControlButtons.prototype, {
    /**
     * Setup the component and load initial washing type data.
     */
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
        this.dialog = useService("dialog");
        this.orm = useService("orm");
        this.loadDataFromWashingTypeModel();
    },
    onWashingClick() {
        this.dialog.add(LaundryServiceTypePopup, {
            title: _t("Laundry Service"),
            body: _t("Choose the Washing type"),
            service: this.pos.washing_type,
            pos: this.pos,
            orderline: this.props.line,
        });
    },

    /**
     * Load washing type details from the backend.
     */
    async loadDataFromWashingTypeModel() {
        const washing_type_data = await this.orm.call(
            "washing.type",
            "search_read",
            [],
            {
                fields: ["name", "assigned_person_id", "amount", "id"],
            }
        );

        this.pos.washing_type = washing_type_data;
    }

});
