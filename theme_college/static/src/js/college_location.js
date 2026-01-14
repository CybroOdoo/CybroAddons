/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";

publicWidget.registry.CollegeLocation = animations.Animation.extend({
    selector: '.college_location_class',
    async start() {
        await this._super(...arguments);
        const self = this;

        try {
            const data = await rpc('/get_college_locations', {});
            if (data) {
                self.$target.empty().append(data);
            }
        } catch (error) {
            console.error('Error fetching college locations:', error);
        }
    }
});

export default publicWidget.registry.CollegeLocation;