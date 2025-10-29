/** @odoo-module */

import { renderToElement } from "@web/core/utils/render";
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.get_product_tab = publicWidget.Widget.extend({
    selector : '.product_tab_body',
    async willStart() {
        const result = await rpc('/get_product_tab', {});
        if(result){
            this.$target.empty().html(renderToElement('theme_boec.product_tab', {result: result}))
        }
    }
});
