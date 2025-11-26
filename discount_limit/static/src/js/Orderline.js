/** @odoo-module */
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { patch } from "@web/core/utils/patch";
import { parseFloat as oParseFloat } from "@web/views/fields/parsers";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";


patch(PosOrderline.prototype, {
    setup() {
        super.setup(...arguments);
    },
    set_discount(discount) {
        /**Add Popup error when Discount Limit is applied for POS Orderline**/
        var order = this.order_id;
        if (order) {
            var pos_prod_id = order.get_selected_orderline().product_id.pos_categ_ids[0]
            if (order.config.apply_discount_limit == false) {
                var parsed_discount =
                    typeof discount === "number" ?
                    discount :
                    isNaN(parseFloat(discount)) ?
                    0 :
                    oParseFloat("" + discount);
                var disc = Math.min(Math.max(parsed_discount || 0, 0), 100);
                this.discount = disc;
                this.discountStr = "" + disc;
            } else if (order.config.apply_discount_limit == 'product_category') {
                var rounded = Math.round(discount);
                if (Number.isInteger(pos_prod_id.id)) {
                    if (this.get_product().pos_categ_ids[0].discount_limit) {
                        if (rounded > this.get_product().pos_categ_ids[0].discount_limit) {
                            return {
                                title: _t("Discount Not Possible"),
                                body: _t(
                                    "You cannot apply discount above the discount limit."
                                ),
                            };
                        } else {
                            var parsed_discount =
                                typeof discount === "number" ?
                                discount :
                                isNaN(parseFloat(discount)) ?
                                0 :
                                oParseFloat("" + discount);
                            var disc = Math.min(Math.max(parsed_discount || 0, 0), 100);
                            this.discount = disc;
                            this.discountStr = "" + disc;
                        }
                    } else {
                        var parsed_discount =
                            typeof discount === "number" ?
                            discount :
                            isNaN(parseFloat(discount)) ?
                            0 :
                            oParseFloat("" + discount);
                        var disc = Math.min(Math.max(parsed_discount || 0, 0), 100);
                        this.discount = disc;
                        this.discountStr = "" + disc;
                    }
                }
            } else if (order.config.apply_discount_limit == 'product') {
                var rounded = Math.round(discount);
                if (Number.isInteger(pos_prod_id.id)) {
                    if (this.get_product().product_discount_limit) {
                        if (rounded > this.get_product().product_discount_limit) {
                            return {
                                title: _t("Discount Not Possible"),
                                body: _t(
                                    "You cannot apply discount above the discount limit."
                                ),
                            };
                        } else {
                            var parsed_discount =
                                typeof discount === "number" ?
                                discount :
                                isNaN(parseFloat(discount)) ?
                                0 :
                                oParseFloat("" + discount);
                            var disc = Math.min(Math.max(parsed_discount || 0, 0), 100);
                            this.discount = disc;
                            this.discountStr = "" + disc;
                        }
                    } else {
                        var parsed_discount =
                            typeof discount === "number" ?
                            discount :
                            isNaN(parseFloat(discount)) ?
                            0 :
                            oParseFloat("" + discount);
                        var disc = Math.min(Math.max(parsed_discount || 0, 0), 100);
                        this.discount = disc;
                        this.discountStr = "" + disc;
                    }
                }
            }
        }
    },
});
