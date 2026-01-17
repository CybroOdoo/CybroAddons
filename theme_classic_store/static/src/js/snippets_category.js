/** @odoo-module **/

import { renderToElement } from "@web/core/utils/render";
import { rpc } from "@web/core/network/rpc";
import PublicWidget from "@web/legacy/js/public/public_widget";

PublicWidget.registry.categories = PublicWidget.Widget.extend({
    selector : '.main_snippet_section',
    async willStart() {
       const result = await rpc('/classic_product_category', {});
       if(result){
           this.$target.empty().html(renderToElement('theme_classic_store.s_classic_store_categories_snippet', {result: result}))
       }
   }
});