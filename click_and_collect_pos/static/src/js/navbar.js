/** @odoo-module **/
import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";

//Patching Navbar to show the Sale Order Screen
patch(Navbar.prototype, {
    setup() {
        super.setup();
    },
    async onClick() {
        var self = this;
        var sale_order = [] ;
        var session_id = self.pos.config.id;
        var stock_picking = this.pos.models['stock.picking'].getAll();
        var sale_order_line = await rpc("/web/dataset/call_kw", {
            model: "sale.order.line",
            method: "search_read",
            args: [],
            kwargs: {},
        });
        sale_order_line.forEach(function (object) {
             if (object.state == "sale" && object.pos_config_id && object.pos_config_id[0] == session_id) {
                stock_picking.forEach(function (lines) {
                if (lines.is_click_and_collect_order){
                    let plan_arr = null;
                    plan_arr = lines.move_ids_without_package.flat(1);
                    plan_arr.forEach(function (line) {
                        if (line.sale_line_id && object.id == line.sale_line_id.id && line.state != "done" ) {
                            sale_order.push(object);
                        }
                    })
                }
                })
             }
        })
        self.pos.showScreen("SaleOrderScreen", {
            click_and_collect: sale_order,
        });
    },
});
