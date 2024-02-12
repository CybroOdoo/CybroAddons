/** @odoo-module **/
import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { jsonrpc } from "@web/core/network/rpc_service";
import { patch } from "@web/core/utils/patch";

patch(Navbar.prototype, {
    setup() {
        super.setup();
    },
    async onClick() {
        var self = this;
        var sale_order = [];
        var stock_picking = self.pos.stock_picking;
        var session_id = self.pos.pos_session.config_id
        var sale_order_line = await jsonrpc("/web/dataset/call_kw", {
            model: "sale.order.line",
            method: "search_read",
            args: [],
            kwargs: {},
        });
        sale_order_line.forEach(function (object) {
            if (object.state == "sale" && session_id[0] == object.pos_config_id[0]) {
                  stock_picking.forEach(function (lines) {
                    let plan_arr = null;
                    plan_arr = lines.move_ids_without_package.flat(1);
                    plan_arr.forEach(function (line) {
                        if (object.id == line.sale_line_id[0] && line.state != "done" ) {
                            sale_order.push(object);
                        }
                    });
                    });
                    }
                     });
        self.pos.showScreen("SaleOrderScreen", {
            click_and_collect: sale_order,
        });
    },
});
