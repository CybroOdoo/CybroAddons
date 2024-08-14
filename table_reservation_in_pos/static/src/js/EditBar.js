/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { FloorScreen } from "@pos_restaurant/app/floor_screen/floor_screen";
import { TextAreaPopup } from "@point_of_sale/app/utils/input_popups/textarea_popup";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { _t } from "@web/core/l10n/translation";

patch(FloorScreen.prototype, {
    async reserve() {
            // Function for reserve table in pos with entering details
            const tables = this.selectedTables;
            const table = tables[0];
            if (!table) return;
            if (table.reserved){
                await this.popup.add(ErrorPopup, {
                    title: _t('Reserved'),
                    body: _t('This table is reserved'),
                });
                return;
            }
            const { confirmed, payload: details } = await this.popup.add(TextAreaPopup, {
                startingValue: _t(''),
                title: _t('Reservation Details ?'),
            });
            if (!confirmed) return;
            await this._reserveTable(table.id, details);
            table.reserved = true;
            table.reservation_details = details;
            await this._save(table);
        },
       async vieInfo() {
            // Function for view reservation details and un reserve table in pos
            const tables = this.selectedTables;
            const table = tables[0];
            if (!table) return;
            if (table.reserved){
                var info = table.reservation_details
                const { confirmed } = await this.popup.add(ConfirmPopup, {
                    title: _t('Reservation Details'),
                    body: _t(info),
                    confirmText: _t('UnReserve'),
                });
                if (confirmed){
                    const { confirmed } = await this.popup.add(ConfirmPopup, {
                        title: _t('Confirm Unreservation'),
                        body: _t('Are you sure you want to unreserve this table?'),
                        confirmText: _t('Yes'),
                        cancelText: _t('No'),
                    });
                    if (confirmed){
                        await this._unReserveTable(table.id);
                        table.reserved = false;
                        table.reservation_details = '';
                        await this._save(table);
                    }
                }
                return;
            }
       },
       async un_reserve() {
            // Function for un reserve reserved table in pos
            const tables = this.selectedTables;
            const table = tables[0];
            if (!table) return;
            if (table.reserved){
                const { confirmed } = await this.popup.add(ConfirmPopup, {
                    title: _t('Confirm Unreservation'),
                    body: _t('Are you sure you want to unreserve this table?'),
                    confirmText: _t('Yes'),
                    cancelText: _t('No'),
                });
                if (confirmed){
                    await this._unReserveTable(table.id);
                    table.reserved = false;
                    table.reservation_details = '';
                    await this._save(table);
                }
            }
        },
        async _reserveTable(tableId, details) {
            // Function for reserve table.
            await this.orm.call("restaurant.table", "reserve_table", [tableId, details]);
        },
        async _unReserveTable(tableId) {
            // Function for un reserve table.
            await this.orm.call("restaurant.table", "un_reserve_table", [tableId]);
        },
});
