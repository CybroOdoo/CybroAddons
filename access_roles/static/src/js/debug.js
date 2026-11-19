/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { LoadingIndicator } from "@web/webclient/loading_indicator/loading_indicator";
import { useService } from "@web/core/utils/hooks";
import { router } from "@web/core/browser/router";
import { onWillStart } from "@odoo/owl";

patch(LoadingIndicator.prototype, {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        if (odoo.debug) {
            onWillStart(async () => {
                try {
                    const result = await this.orm.call(
                        "role.management",
                        "get_role_restrictions",
                    );
                    if (result.is_debug) {
                        this.notification.add(
                            "You are not allowed to enter debug mode. Please contact Administration.",
                            { type: "danger" }
                        );
                        router.pushState({ debug: 0 }, { reload: true });
                    }
                } catch {
                    // Fail gracefully when restriction cannot be fetched
                }
            });
        }
        super.setup();
    },
});
