odoo.define('pos_all_orders.PartnerLine', function (require) {
    'use strict';

    const PartnerLine = require('point_of_sale.PartnerLine');
    const Registries = require('point_of_sale.Registries');
    const { useListener } =require("@web/core/utils/hooks");
    var rpc = require('web.rpc');

    const PosOrderPartnerLine = (PartnerLine) =>
        class extends PartnerLine {
            setup(){
                super.setup();
                useListener('click-order', this._onClickOrder);
                }
            async _onClickOrder(id) {
                var self = this
                var order = this.env.pos.pos_orders
                var orders = []
                for (let i = 0; i < order.length; i++) {
                    if (order[i].partner_id[0] == id){
                        orders.push(order[i])
                    }
                }
                this.showScreen('CustomALLOrdrScreen', {
                    orders: orders,
                });
            }

        };

    Registries.Component.extend(PartnerLine, PosOrderPartnerLine);

    return PartnerLine;
});
