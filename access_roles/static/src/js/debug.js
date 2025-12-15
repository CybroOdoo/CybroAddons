/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { LoadingIndicator } from "@web/webclient/loading_indicator/loading_indicator";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";
import { onWillStart} from "@odoo/owl";

patch(LoadingIndicator.prototype, {
    setup() {
        this.orm = useService("orm");
        this.router = useService("router");

        if (odoo.debug) {
            onWillStart(async () => {
                try {
                    const userId = session.uid;
                    const result = await this.orm.call(
                        "role.management",
                        "get_role_restrictions",
                        [userId]
                    );
                    if (result && result.is_debug) {
                     alert('You are not allowed to enter debug mode. Please contact Administration.');
                     this.router.pushState({ debug: 0 }, { reload: true });
                   }
                } catch (error) {
                    console.error("Error checking debug permission:", error);
                }
            });
        }
        super.setup();
    },
});