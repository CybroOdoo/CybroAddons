/** @odoo-module */
/**
 * This file will used to hide the selected options from the list view
 */
import { ListController } from '@web/views/list/list_controller';
import { patch } from "@web/core/utils/patch";
import { user } from "@web/core/user";
const { onWillStart } = owl;

patch(ListController.prototype, {
       /**
     * This function is used to hide the selected options from the list view
     */
    setup() {
        super.setup(...arguments);
        this.rpc = this.env.services.rpc;
        onWillStart(async () => {
            this.user = user;
            var self = this;
            var result;
            result = await this.env.services.orm.silent.call(
                "access.right",
                "hide_buttons",
            );

            for (var i = 0; i < result.length; i++) {
                var group = result[i].module + "." + result[i].group_name;

                if (self.props.resModel == result[i].model) {
                    if (result[i].restriction_type == "group") {
                        if (await self.user.hasGroup(group)) {
                            if (!this.user.isAdmin) {
                                if (result[i].is_create_or_update) {
                                    self.activeActions.create = false;
                                }
                                if (result[i].is_export) {
                                    self.isExportEnable = false;
                                }
                                if (result[i].is_delete) {
                                    self.activeActions.delete = false;
                                }
                                if (result[i].is_archive) {
                                    self.activeActions.archive = false;
                                    self.isArchiveRestricted = true;
                                }
                            }
                        }
                    } else {
                        if (await self.user.userId == result[i].user[0]) {
                            if (!this.user.isAdmin) {
                                if (result[i].is_create_or_update) {
                                    self.activeActions.create = false;
                                }
                                if (result[i].is_export) {
                                    self.isExportEnable = false;
                                }
                                if (result[i].is_delete) {
                                    self.activeActions.delete = false;
                                }
                                if (result[i].is_archive) {
                                    self.activeActions.archive = false;
                                    self.isArchiveRestricted = true;
                                }
                            }
                        }
                    }
                }
            }
        });
    },

    get actionMenuItems() {
        const menuItems = super.actionMenuItems;

        if (!this.isArchiveRestricted) {
            return menuItems;
        }

        // Clone and filter menu items
        const filteredMenuItems = {};

        for (const section in menuItems) {
            if (Array.isArray(menuItems[section])) {
                filteredMenuItems[section] = menuItems[section].filter(item => {
                    const key = item.key || item.description;
                    return key !== "archive" && key !== "unarchive";
                });
            } else {
                filteredMenuItems[section] = menuItems[section];
            }
        }

        return filteredMenuItems;
    },

    getOptionalActiveFields() {
        const result = super.getOptionalActiveFields();
        if (this.isArchiveRestricted && result) {
            // Remove archive field from optional active fields if restricted
            return result.filter(field => field !== 'active');
        }
        return result;
    }
});
