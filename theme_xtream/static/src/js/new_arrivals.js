/** @odoo-module **/
import PublicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { renderToFragment } from "@web/core/utils/render";

var NewArrivalsWidget = PublicWidget.Widget.extend({
    selector: '.new_arrivals',  // Add this class to your snippet container
    willStart: async function () {
        const data = await rpc('/get_arrival_product', {});
        this.$el.html(renderToFragment('theme_xtream.s_new_arrivals', {
            new_arrivals: data.new_arrivals || [],
        }));
    },
});

PublicWidget.registry.new_arrivals_widget = NewArrivalsWidget;
export default NewArrivalsWidget;
