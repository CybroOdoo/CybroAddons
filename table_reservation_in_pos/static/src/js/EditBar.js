import { patch } from "@web/core/utils/patch";
import { FloorPlanEditor } from "@pos_restaurant/app/screens/floor_screen/floor_plan_editor/floor_plan_editor";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { TextInputPopup } from "@point_of_sale/app/components/popups/text_input_popup/text_input_popup";
import { AlertDialog, ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(FloorPlanEditor.prototype, {
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
    },

    /**
     * Whether table reservation is enabled in the POS configuration.
     */
    get isTableReservationEnabled() {
        return Boolean(this.pos.config.table_reservation);
    },

    /**
     * Return the selected table record, or undefined when the feature is
     * disabled or no table is selected.
     */
    _getSelectedTable() {
        if (!this.isTableReservationEnabled) {
            return undefined;
        }
        const tableElement = this.selectedElement;
        if (!tableElement || !tableElement.isTable) {
            return undefined;
        }
        return tableElement.record;
    },

    async reserve() {
        const table = this._getSelectedTable();
        if (!table) {
            return;
        }
        if (table.reserved) {
            this.dialog.add(AlertDialog, {
                title: _t("Reserved"),
                body: _t("This table is already reserved."),
            });
            return;
        }
        this.dialog.add(TextInputPopup, {
            title: _t("Reservation Details"),
            placeholder: _t("Enter the reservation details"),
            getPayload: async (details) => {
                await this.pos.data.write("restaurant.table", [table.id], {
                    reserved: true,
                    reservation_details: details,
                });
            },
        });
    },

    async viewInfo() {
        const table = this._getSelectedTable();
        if (!table) {
            return;
        }
        this.dialog.add(AlertDialog, {
            title: table.reserved ? _t("Reservation Details") : _t("Not Reserved"),
            body: table.reserved
                ? table.reservation_details || _t("No details were entered.")
                : _t("This table is not reserved."),
        });
    },

    async unReserve() {
        const table = this._getSelectedTable();
        if (!table || !table.reserved) {
            return;
        }
        this.dialog.add(ConfirmationDialog, {
            title: _t("Confirm Unreservation"),
            body: _t("Are you sure you want to unreserve this table?"),
            confirm: async () => {
                await this.pos.data.write("restaurant.table", [table.id], {
                    reserved: false,
                    reservation_details: "",
                });
            },
        });
    },
});
