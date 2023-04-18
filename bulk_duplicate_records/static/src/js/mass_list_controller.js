/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { ListController } from '@web/views/list/list_controller';
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { download } from "@web/core/network/download";
import { DynamicRecordList } from "@web/views/relational_model";
import { useService } from "@web/core/utils/hooks";
import { sprintf } from "@web/core/utils/strings";
import { ActionMenus } from "@web/search/action_menus/action_menus";
import { Layout } from "@web/search/layout";
import { usePager } from "@web/search/pager_hook";
import { session } from "@web/session";
import { useModel } from "@web/views/model";
import { standardViewProps } from "@web/views/standard_view_props";
import { useSetupView } from "@web/views/view_hook";
import { ViewButton } from "@web/views/view_button/view_button";
import { useViewButtons } from "@web/views/view_button/view_button_hook";
import { ExportDataDialog } from "@web/views/view_dialogs/export_data_dialog";

const { Component, onWillStart, useSubEnv, useEffect, useRef } = owl;

//Created new button mass duplicate and function for duplicate multiple records
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
                description: this.env._t("Mass duplicate"),
                callback: (x) => {
                    this._onDuplicateSelectedRecords();
                }
            });
        }
        return actionMenuItems;
    }
});
