/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Widget: AskedQuestions
 * Description:
 *   - Fetches dynamic FAQ content from the backend via RPC.
 *   - Updates the `.faq` container with the returned HTML.
 */

publicWidget.registry.AskedQuestions = publicWidget.Widget.extend({
    selector: '.faq',

    async start() {
        await this._super(...arguments);
        const data = await rpc('/get_asked_questions', {});
        if (data) {
            this.$target.html(data);
        }
    },
});

