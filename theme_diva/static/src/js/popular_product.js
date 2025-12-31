/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.divaIndexProduct = publicWidget.Widget.extend({
    selector: '.main_product_snippet_class',

    start() {
        return this._super(...arguments).then(() => {
            this._loadProducts();
        });
    },

    _loadProducts() {
        this.$target.empty();
        $.get("/diva_index_main_product_data").then((data) => {
            this.$target.append(data);
        });
    },
});
