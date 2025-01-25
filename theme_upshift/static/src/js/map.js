/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import { generateGMapLink } from '@website/js/utils';
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.Map_1 = publicWidget.Widget.extend({
    selector: '.s_map.s_map_1',

    // Fallback address if no company address is found
    FALLBACK_ADDRESS: '250 Executive Park Blvd, Suite 3400 San Francisco California (US) United States',

    /**
     * @override
     */
    async start() {
        let address;
        try {
            address = await rpc("/get-company/address");
        } catch (error) {
            console.warn('Failed to fetch company address, using fallback', error);
        }

        // Use fallback address if no address is retrieved
        address = address || this.FALLBACK_ADDRESS;

        const existingIframe = this.el.querySelector('.s_map.s_map_1 iframe');
        if (existingIframe) {
            existingIframe.remove();
        }

        const iframeEl = document.createElement('iframe');
        iframeEl.classList.add('s_map_embedded', 'o_not_editable');
        iframeEl.setAttribute('width', '100%');
        iframeEl.setAttribute('height', '350');
        iframeEl.setAttribute('frameborder', '0');
        iframeEl.setAttribute('style', 'border:0;');
        iframeEl.setAttribute('allowfullscreen', '');
        iframeEl.setAttribute('aria-hidden', 'false');
        iframeEl.setAttribute('tabindex', '0');

        iframeEl.setAttribute('src', generateGMapLink({
            mapType: 'm',
            mapZoom: "12",
            name: 'Map',
            snippet: 's_map',
            mapAddress: address
        }));

        this.el.querySelector('.s_map_color_filter_1').before(iframeEl);
    },
});

export default publicWidget.registry.Map_1;