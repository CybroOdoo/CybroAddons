/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

const CarouselDashboard = publicWidget.Widget.extend({
    selector: '.s_carousel_template',
    start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            rpc('/get_dashboard_carousel', {})
                .then(function (data) {
                    if (data) {
                        self.$target.empty().append(data);
                    }
                });
        });
    }
});

publicWidget.registry.get_dashboard_carousel = CarouselDashboard;
export default CarouselDashboard;
