/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
publicWidget.registry.determine_checkout = publicWidget.Widget.extend({
    selector: '#wrap',
    init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
    },
    willStart: function () {
        var self = this;
                    this.$el.find('#o_demo_express_checkout_container_6').css('display', 'none')
        return this._super(...arguments);
    },
});