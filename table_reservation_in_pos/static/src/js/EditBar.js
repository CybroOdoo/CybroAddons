/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { FloorScreen } from "@pos_restaurant/app/screens/floor_screen/floor_screen";
import { TextInputPopup } from "@point_of_sale/app/components/popups/text_input_popup/text_input_popup";
import { AlertDialog, ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(FloorScreen.prototype, {
    async reserve() {
            // Function for reserve table in pos with entering details
            const tables = this.selectedTables;
            const table = tables[0];
            if (!table) return;
            if (table.reserved){
                this.dialog.add(AlertDialog, {
                    title: _t("Reserved"),
                    body: _t(
                        "This table is reserved"
                    ),
                });
                return;
            }
            this.dialog.add(TextInputPopup, {
                title: _t("Reservation Details ?"),
                placeholder: _t("reservation details"),
                getPayload: async (details) => {
                    this.pos.data.write("restaurant.table", [table.id], { reserved: true, reservation_details: details });
                },
            });
        },
       async viewInfo() {
            // Function for view reservation details
            const tables = this.selectedTables;
            const table = tables[0];
            if (!table) return;
            if (table.reserved){
                var info = table.reservation_details
                this.dialog.add(AlertDialog, {
                    title: _t("Reservation Details"),
                    body: info,
                });
                return;
            }
       },
       async un_reserve() {
            // Function for un reserve reserved table in pos
            const tables = this.selectedTables;
            const table = tables[0];
            if (!table) return;
            if (table.reserved){
                this.dialog.add(ConfirmationDialog, {
                    title: _t('Confirm Unreservation'),
                    body: _t('Are you sure you want to unreserve this table?'),
                    confirm: async () => {
                        this.pos.data.write("restaurant.table", [table.id], { reserved: false, reservation_details: '' });
                    },
                });
            }
        },
});
