/** @odoo-module */

import { ListController} from '@web/views/list/list_controller';
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";
import { onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

patch(ListController.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        onWillStart(async () => {
            const userId = session.uid;
            const restrictions = await this.orm.call("role.management", "get_export_restrictions", [userId]);
            restrictions.forEach(result => {
                if (this.props.resModel === result.model && result.is_hide_export) {
                    this.isExportEnable = false;
                }
                if (this.props.resModel === result.model && result.is_hide_archive) {
                    this.archiveEnabled = false;
                }
            });
        });
    }
});