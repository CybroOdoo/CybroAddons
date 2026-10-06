/** @odoo-module **/

import { renderToElement } from "@web/core/utils/render";
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

function chunk(array, size) {
    const chunks = [];
    for (let i = 0; i < array.length; i += size) {
        chunks.push(array.slice(i, i + size));
    }
    return chunks;
}

publicWidget.registry.AwardsStuff = publicWidget.Widget.extend({
    selector: '.s_awards_and_stuff',
    async willStart() {
        const result = await jsonrpc('/awards_stuff', {});
        if (result.awards.length > 0) {
            const chunks = chunk(result.awards, 3);  // 3 awards per slide
            chunks[0].is_active = true;
            const uniq = Date.now();
            this.$target.empty().html(renderToElement(
                'theme_educational.awards_and_stuff_snippet',
                {
                    award_chunks: chunks,
                    uniq: uniq,
                }
            ));
        }
    },
});
