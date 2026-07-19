import { RestaurantTable } from "@pos_restaurant/app/models/restaurant_table";
import { FloorScreen } from "@pos_restaurant/app/screens/floor_screen/floor_screen";
import { TextInputPopup } from "@point_of_sale/app/components/popups/text_input_popup/text_input_popup";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { ReceiptHeader } from "@point_of_sale/app/screens/receipt_screen/receipt/receipt_header/receipt_header";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

/**
 * Enhanced Table Model Patch
 */
const tablePatch = {
    setup(rawData) {
        super.setup(rawData);
        this.table_alias = rawData.table_alias || `${this.table_number}`;
    },

    fetchTableAlias() {
        return this.table_alias || `${this.table_number}`;
    }
};
patch(RestaurantTable.prototype, tablePatch);

/**
 * Floor Screen Business Logic
 */
patch(FloorScreen.prototype, {
    async renameTable() {
        const targetRow = this.selectedTables[0];
        if (!targetRow) return this.renameFloor();

        this.dialog.add(TextInputPopup, {
            title: _t("Confirm Table Name"),
            startingValue: targetRow.fetchTableAlias(),
            placeholder: _t("Example: A10, B20, VIP"),
            getPayload: (inputVal) => {
                if (inputVal !== undefined && inputVal !== targetRow.table_alias) {
                    this.pos.data.write("restaurant.table", [targetRow.id], {
                        table_alias: inputVal,
                    });
                }
            },
        });
    }
});

/**
 * POS Checkout & Orders Logic
 */
patch(PosOrder.prototype, {
    getName() {
        const orderInstance = this.getTable();
        if (!this.config.module_pos_restaurant || !orderInstance) {
            return super.getName();
        }

        let labelString = orderInstance.table_alias || orderInstance.table_number;

        const linkedItems = this.models["restaurant.table"].filter(
            entry => entry.floor_id?.id === orderInstance.floor_id?.id && orderInstance.isParent(entry)
        );

        if (linkedItems.length > 0) {
            const extraLabels = linkedItems.map(item => item.table_alias || item.table_number).join('.');
            return `${labelString}.${extraLabels}`;
        }
        return `${labelString}`;
    }
});

/**
 * Receipt Branding Overrides
 */
patch(ReceiptHeader.prototype, {
    get getReceiptTableData() {
        const sessionOrder = this.order;
        const currentTbl = sessionOrder.table_id || sessionOrder.self_ordering_table_id;
        if (!currentTbl) return "";

        const codeVal = currentTbl.table_alias || currentTbl.table_number;
        const guestInfo = sessionOrder.customer_count ? ` [${sessionOrder.customer_count} HeadCount]` : "";

        return `${_t("Table Name")}: ${codeVal}${guestInfo}`;
    }
});
