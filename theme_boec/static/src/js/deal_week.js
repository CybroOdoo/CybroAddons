/** @odoo-module **/

import { renderToElement } from "@web/core/utils/render";
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

//created a public widget class for deal week snippet
publicWidget.registry.DealWeek = publicWidget.Widget.extend({
    selector: '.deal_week_snippet_class',
    async start() {
        await this._super(...arguments);
        const result = await rpc("/get_products", {});
        if (result){
            this.$target.empty().html(renderToElement('theme_boec.deal_week', {product_id: result}))
            const time = await rpc("/get_countdown", {});
            if (time){
                let end_date = new Date(time).getTime();
                let days, hours, minutes, seconds;
                let countdown_div = this.$el.find('#countdown')[0];
                setInterval(function() {
                    const current_date = new Date().getTime();
                    let seconds_left = (end_date - current_date) / 1000;
                    days = parseInt(seconds_left / 86400);
                    seconds_left = seconds_left % 86400;
                    hours = parseInt(seconds_left / 3600);
                    seconds_left = seconds_left % 3600;
                    minutes = parseInt(seconds_left / 60);
                    seconds = parseInt(seconds_left % 60);
                    if (countdown_div) {
                        countdown_div.innerHTML = '<span class="days">' + days + ' <label>Days</label></span> <span class="hours">' + hours + ' <label>Hours</label></span> <span class="minutes">' +
                            minutes + ' <label>Minutes</label></span> <span class="seconds">' + seconds + ' <label>Seconds</label></span>';
                    }
                }, 1000);
            }
        }

    },
});

//export default publicWidget.registry.DealWeek;