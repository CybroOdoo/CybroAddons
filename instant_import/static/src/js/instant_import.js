/** @odoo-module **/

import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { ImportRecords } from "@base_import/import_records/import_records";

patch(ImportRecords.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
    },
    async InstantImport() {
        const { context, resModel } = this.env.searchModel;
        this.action.doAction({
            type: "ir.actions.client",
            tag: "instant_import",
            params: { model: resModel, context },
        });
    }
});