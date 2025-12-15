/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { Chatter } from "@mail/core/web/chatter";
import { session } from "@web/session";
import { onRendered, useRef } from "@odoo/owl";

const ChatterPatch = {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.chatterRef = useRef("chatter");
        // Once the chatter component is mounted, check user preferences
        onRendered(async () => {
            try {
                const userId = session.uid;
                 const userData = await this.orm.call(
                    "role.management",
                    "get_role_restrictions",
                    [userId]
                );
                if (userData.is_chatter === true && this.rootRef?.el) {
                    setTimeout(() => {
                        if (this.rootRef?.el) {
                            this.rootRef.el.classList.add("d-none");
                        }
                    }, 0);
                }
            } catch (error) {
                console.error("Failed to check chatter visibility preference:", error);
            }
        });
    },
};
patch(Chatter.prototype, ChatterPatch);