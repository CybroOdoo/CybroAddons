/** @odoo-module **/

import { renderToElement } from "@web/core/utils/render";
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.DealWeek = publicWidget.Widget.extend({
   selector : '.lego_week_deals_main_section',
   async willStart() {
       const result = await rpc('/get_deal_of_the_week', {});
       if(result){
           this.$target.empty().html(renderToElement('theme_lego.lego_deals', {result: result}))
       }
   },
});