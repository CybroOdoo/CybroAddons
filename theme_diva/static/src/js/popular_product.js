/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";

publicWidget.registry.divaIndexProduct = animations.Animation.extend({
    selector: '.main_product_snippet_class',
    async start() {
        $.get("/diva_index_main_product_data", (data) => {
            this.$target.empty().append(data);
        });
    }
});
