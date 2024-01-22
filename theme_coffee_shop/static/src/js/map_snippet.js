/** @odoo-module **/

import publicWidget from 'web.public.widget';
import {generateGMapLink, generateGMapIframe} from 'website.utils';

publicWidget.registry.Map_1 = publicWidget.Widget.extend({
    selector: '.s_map.s_map_1',

    /**
     * @override
     */
    async start() {
            console.log("kkkkk")
            const address = await this._rpc({
                route: "/get-company/address",
            });

            const existingIframe = this.el.querySelector('.s_map.s_map_1 iframe');
            if (existingIframe) {
                existingIframe.remove();
            }

            if (address) {
                const iframeEl = generateGMapIframe();
                iframeEl.setAttribute('src', generateGMapLink({mapType: 'm', mapZoom: "12", name: 'Map', snippet: 's_map', mapAddress: address}));
                this.el.querySelector('.s_map_color_filter_1').before(iframeEl);
            }
    },

});

export default publicWidget.registry.Map_1;
