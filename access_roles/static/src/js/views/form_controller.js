/** @odoo-module */

import { FormController } from '@web/views/form/form_controller';
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";
import { onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");

        // Custom flag
        this.isArchiveEnable = true;

        onWillStart(async () => {
            const userId = session.uid;
            const restrictions = await this.orm.call("role.management", "get_export_restrictions", [userId]);
            restrictions.forEach(result => {
                if (this.props.resModel === result.model) {
                    if (result.is_hide_archive) {
                        this.isArchiveEnable = false;
                    }
                }
            });
        });
        // Patch getStaticActionMenuItems to conditionally exclude archive/unarchive
        if (this.getStaticActionMenuItems) {
            const originalGetStaticActionMenuItems = this.getStaticActionMenuItems.bind(this);
            this.getStaticActionMenuItems = (...args) => {
                const items = originalGetStaticActionMenuItems(...args);
                if (!this.isArchiveEnable) {
                    // Remove archive and unarchive from the static items
                    delete items.archive;
                    delete items.unarchive;
                }
                return items;
            };
        }
    }
});