/** @odoo-module **/

import { Store } from "@mail/core/common/store_service";
import { patch } from "@web/core/utils/patch";

patch(Store.prototype, {
    /**
     * Override getMessagePostParams to preserve selected_follower_partner_ids
     * The original method reconstructs postData and drops unknown keys.
     */
    async getMessagePostParams({ body, postData, thread }) {
        const params = await super.getMessagePostParams(...arguments);

        // Check if the original postData had our custom whitelist
        if (postData.selected_follower_partner_ids) {
            // Inject it into the result params.post_data
            if (!params.post_data) {
                params.post_data = {};
            }
            params.post_data.selected_follower_partner_ids = postData.selected_follower_partner_ids;
        }
        return params;
    },
});
