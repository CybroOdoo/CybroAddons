import { RestaurantTable } from "@pos_restaurant/app/models/restaurant_table";
import { EditTableProperties } from "@pos_restaurant/app/screens/floor_screen/floor_plan_editor/edit_table/edit_table";
import { FloorTable } from "@pos_restaurant/app/services/floor_plan/elements/table";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { GeneratePrinterData } from "@point_of_sale/app/utils/printer/generate_printer_data";
import { patch } from "@web/core/utils/patch";

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
 * Edit Table Properties Logic
 */
patch(EditTableProperties.prototype, {
    updateTableAlias(event) {
        this.updateTable({ table_alias: event.target.value });
    }
});

patch(FloorTable.prototype, {
    get table_alias() {
        return this._table_alias ?? (this.record && this.record.table_alias) ?? '';
    },
    set table_alias(val) {
        this._table_alias = val;
    },
    get raw() {
        const res = super.raw;
        res.table_alias = this.table_alias;
        return res;
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
patch(GeneratePrinterData.prototype, {
    get commonExtraData() {
        const extraData = super.commonExtraData;
        if (this.config.module_pos_restaurant) {
            const table = this.order.table_id || this.order.self_ordering_table_id;
            if (table) {
                const codeVal = table.table_alias || table.table_number;
                const guestInfo = this.order.customer_count ? ` [${this.order.customer_count} HeadCount]` : "";
                extraData.table_name = guestInfo ? `${codeVal}${guestInfo}` : codeVal;
            }
        }
        return extraData;
    }
});
