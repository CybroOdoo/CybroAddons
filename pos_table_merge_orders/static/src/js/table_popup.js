/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";

export class MergeTablePopup extends AbstractAwaitablePopup {
    static template = "pos_table_merge_orders.MergeTablePopup";
    static defaultProps = {
        confirmText: _t("Add"),
        cancelText: _t("Discard"),
        title: "",
        body: "",
    };
    setup() {
        super.setup();
        this.selectedTable = [];
    }
//    return the selected tables to the productscreen
    getPayload() {
        return this.selectedTable;
    }

//    get the current tables from this floor
    get tables() {
        var tables = [];
        var floors = this.pos.floors
        floors.tables.forEach(item => {
            tables.push({'id':item.id, 'name':item.name})
        })
        return tables;
    }

    // Event for selecting the tables
    click_on_merge_table(event) {
        var self = this;
        if ($(event.target).data('click') == '1') {
            $(event.target).data('click', '0');
            $(event.target).css("background-color", "#fff"); // css for showing selected tables.
            var index = this.selectedTable.indexOf($(event.target).data('table_id'));
            if (index !== -1) {
                this.selectedTable.splice(index, 1);
             }
        }
        else{
            $(event.target).data('click','1')
            this.selectedTable.push($(event.target).data('table_id'))
            $(event.target).css("background-color", "#90EE90");
        }
    }
}
