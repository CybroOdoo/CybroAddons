/**
 * This file is used to hide the selected options from the list view
 */
import { ListController } from '@web/views/list/list_controller';
import { patch } from "@web/core/utils/patch";
import { user } from "@web/core/user";
import { registry } from "@web/core/registry";
import { onWillStart } from "@odoo/owl";

patch(ListController.prototype, {
    /**
     * This function is used to hide the selected options from the list view
     */
    setup() {
        super.setup(...arguments);
        onWillStart(async () => {
            this.user = user;
            const result = await this.env.services.orm.silent.call(
                "access.right",
                "hide_buttons",
            );

            for (const item of result) {
                const group = `${item.module}.${item.group_name}`;

                if (this.props.resModel === item.model) {
                    if (item.restriction_type === "group") {
                        if (await this.user.hasGroup(group)) {
                            if (!this.user.isAdmin) {
                                if (item.is_create_or_update) {
                                    this.activeActions.create = false;
                                }
                                if (item.is_export) {
                                    this.isExportEnable = false;
                                }
                                if (item.is_delete) {
                                    this.activeActions.delete = false;
                                }
                                if (item.is_archive) {
                                    this.activeActions.archive = false;
                                    this.isArchiveRestricted = true;
                                }
                            }
                        }
                    } else {
                        if (this.user.userId === item.user[0]) {
                            if (!this.user.isAdmin) {
                                if (item.is_create_or_update) {
                                    this.activeActions.create = false;
                                }
                                if (item.is_export) {
                                    this.isExportEnable = false;
                                }
                                if (item.is_delete) {
                                    this.activeActions.delete = false;
                                }
                                if (item.is_archive) {
                                    this.activeActions.archive = false;
                                    this.isArchiveRestricted = true;
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

const exportAllItem = registry.category("cogMenu").get("export-all-menu");
if (exportAllItem) {
    const originalIsDisplayed = exportAllItem.isDisplayed;
    exportAllItem.isDisplayed = async (env) => {
        const displayed = await originalIsDisplayed(env);
        if (!displayed) {
            return false;
        }

        try {
            const resModel = env.model && env.model.root && env.model.root.resModel;
            if (!resModel) {
                return true;
            }
            const result = await env.services.orm.silent.call(
                "access.right",
                "hide_buttons",
            );
            for (const item of result) {
                if (resModel === item.model && item.is_export) {
                    if (item.restriction_type === "group") {
                        const group = `${item.module}.${item.group_name}`;
                        if (await user.hasGroup(group) && !user.isAdmin) {
                            return false;
                        }
                    } else {
                        if (user.userId === item.user[0] && !user.isAdmin) {
                            return false;
                        }
                    }
                }
            }
        } catch (_e) {
            // Fallback to allowing export if restriction check encounters an issue
        }
        return true;
    };
}
