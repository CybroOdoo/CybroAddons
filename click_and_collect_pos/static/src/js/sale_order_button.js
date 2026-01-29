odoo.define('click_and_collect_pos.SaleOrderButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    var ajax = require('web.ajax');
    const {useService} = require("@web/core/utils/hooks");

    // Define a new class that extends PosComponent
    class SaleOrderButton extends PosComponent {

        /**
         * Override the setup method to perform any additional setup logic.
         */
        setup() {
            super.setup();
        }

        async onClick() {
//            getting orders
            var self = this;
            var sale_order = [];
            var session_id = self.env.pos.pos_session.id
            var sale_order_line = await this.rpc({
                model: 'sale.order.line',
                method: 'search_read',
                args: [],
                kwargs: {},
            });
            var stock_picking = await this.rpc({
                model: 'stock.move',
                method: 'search_read',
                fields: ['id', 'sale_line_id', 'state'],
                args: [],
                kwargs: {},
            });
            sale_order_line.forEach(function (object) {
                if (object.state == 'sale' && object.is_click_and_collect) {
                    if(self.env.pos.config_id == object.pos_config_id[0]){
                        stock_picking.forEach(function (line) {
                        if (line.sale_line_id[0] && line.state != 'done') {
                            if (object.id == line.sale_line_id[0]) {
                                sale_order.push(object);
                            }
                        }
                    })
                    }
                }
            });
            self.showScreen('SaleOrderScreen', {
                click_and_collect: sale_order,
            });
        }
    }
    SaleOrderButton.template = 'click_and_collect_pos.SaleOrderButton';
    Registries.Component.add(SaleOrderButton);
    return SaleOrderButton;
});