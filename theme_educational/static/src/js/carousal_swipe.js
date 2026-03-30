/** @odoo-module **/

import { renderToElement } from "@web/core/utils/render";
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

function chunk(array, size) {
    const chunks = [];
    for (let i = 0; i < array.length; i += size) {
        chunks.push(array.slice(i, i + size));
    }
    return chunks;
}

publicWidget.registry.TrendingCourses = publicWidget.Widget.extend({
    selector: '.s_top_trending_courses',
    async willStart() {
        const result = await rpc('/latest_products', {});
        if (result.products.length > 0) {
            const chunks = chunk(result.products, 3);
            chunks[0].is_active = true;
            const uniq = Date.now();
            this.$target.empty().html(renderToElement(
                'theme_educational.top_trending_courses_snippet',
                {
                    product_chunks: chunks,
                    uniq: uniq,
                }
            ));
        }
    },
});

