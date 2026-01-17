/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.CollegeLocation = publicWidget.Widget.extend({
    selector: '.college_location_class',

    async start() {
        await this._super(...arguments);

        try {
            const data = await rpc('/get_college_locations', {});
            if (data) {
                this.$el.empty().append(data);
            }
        } catch (error) {
            console.error('Error fetching college locations:', error);
        }
    }
});

export default publicWidget.registry.CollegeLocation;
