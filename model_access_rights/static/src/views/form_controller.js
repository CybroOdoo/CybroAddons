/**
 * This file is used to hide the selected options from the form view
 */
import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { user } from "@web/core/user";
import { onWillStart } from "@odoo/owl";

patch(FormController.prototype, {
    /**
     * This function is used to hide the selected options from the form view
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
                                    this.canCreate = false;
                                }
                                if (item.is_delete) {
                                    this.archInfo.activeActions.delete = false;
                                }
                                if (item.is_archive) {
                                    this.archInfo.activeActions.archive = false;
                                    this.isArchiveRestricted = true;
                                }
                            }
                        }
                    } else {
                        if (this.user.userId === item.user[0]) {
                            if (!this.user.isAdmin) {
                                if (item.is_create_or_update) {
                                    this.canCreate = false;
                                }
                                if (item.is_delete) {
                                    this.archInfo.activeActions.delete = false;
                                }
                                if (item.is_archive) {
                                    this.archInfo.activeActions.archive = false;
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
    }
});
