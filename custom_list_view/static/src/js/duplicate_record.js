/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ListController } from '@web/views/list/list_controller';

const { Component, onWillStart, useSubEnv, useEffect, useRef } = owl;

patch(ListController.prototype, "getActionMenuItems", {
    async _onDuplicateSelectedRecords() {
        for (var record in this.model.root.records) {
            if (this.model.root.records[record].selected) {
                await this.model.root.records[record].duplicate();
            }
        }
        window.location.reload();
    },

    getActionMenuItems() {
        const actionMenuItems = this._super.apply(this, arguments);
        var self = this;
        if (actionMenuItems) {
            actionMenuItems.other.splice(1, 0, {
                description: this.env._t("Duplicate"),
                callback: (x) => {
                    this._onDuplicateSelectedRecords();
                }
            });
        }
        return actionMenuItems;
    }
});