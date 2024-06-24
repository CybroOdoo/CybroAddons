/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.all_type = publicWidget.Widget.extend({
    selector : '.all_type',
    async start() {
        const data = await ajax.jsonRpc('/get_all_type', {})
        if(data){
            this.$target.empty().append(data);
        }
    }
});