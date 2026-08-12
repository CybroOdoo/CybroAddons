/** @odoo-module **/

import { RestaurantTable } from "@pos_restaurant/app/models/restaurant_table";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { FloorScreen } from "@pos_restaurant/app/floor_screen/floor_screen";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

patch(RestaurantTable.prototype, {
    /**
     * Override setup to initialize custom_table_name alongside existing parameters.
     * @param {Object} vals Initial table values.
     */
    setup(vals) {
        super.setup(vals);
        this.custom_table_name = vals.custom_table_name || this.table_number.toString();
    },

    /**
     * Get the restaurant table name for display use in the UI.
     * @returns {string} The custom name of the table or its designated number.
     */
    getName() {
        return this.custom_table_name || this.table_number.toString();
    },
});

patch(FloorScreen.prototype, {
    /**
     * Opens the table renaming configuration screen, allowing users to
     * define an alphanumeric custom_table_name.
     */
    async renameTable() {
        if (this.selectedTables.length !== 1) {
            return super.renameTable();
        }

        const table = this.selectedTables[0];
        this.dialog.add(TextInputPopup, {
            startingValue: table.custom_table_name || table.table_number.toString(),
            title: _t("Change table name?"),
            placeholder: _t("Enter table name (e.g., A1, VIP-1)"),
            getPayload: (assignedTableName) => {
                if (assignedTableName && assignedTableName !== table.custom_table_name) {
                    this.pos.data.write("restaurant.table", [table.id], {
                        custom_table_name: assignedTableName,
                    });
                }
            },
        });
    },
});

patch(PosOrder.prototype, {
    /**
     * Retrieve the composite name of the order, appending custom table names
     * to child tables iteratively.
     * @returns {string} Processed composite table name.
     */
    getName() {
        if (this.config.module_pos_restaurant && this.getTable()) {
            const table = this.getTable();
            const parentName = table.custom_table_name || table.table_number.toString();

            const childNames = this.models["restaurant.table"]
                .filter((t) => t.floor_id.id === table.floor_id.id && table.isParent(t))
                .map((t) => t.custom_table_name || t.table_number.toString());

            return [parentName, ...childNames].join(" & ");
        }
        return super.getName(...arguments);
    },
});

patch(PosStore.prototype, {
    /**
     * Extend receipt header rendering functionality with custom_table_name support.
     * @param {Object} order The reference Point of Sale order object.
     * @returns {Object} JSON receipt header data structure.
     */
    getReceiptHeaderData(order) {
        const json = super.getReceiptHeaderData(...arguments);
        if (this.config.module_pos_restaurant && order) {
            if (order.getTable()) {
                json.table = order.getTable().getName();
            }
        }
        return json;
    }
});
