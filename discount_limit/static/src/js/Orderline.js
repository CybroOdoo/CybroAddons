/** @odoo-module */
import { Orderline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { parseFloat as oParseFloat } from "@web/views/fields/parsers";
import { _t } from "@web/core/l10n/translation";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

patch(Orderline.prototype, {
    setup() {
        super.setup(...arguments);
    },
    set_discount(discount) {
        /**Add Popup error when Discount Limit is applied for POS Orderline**/
        var order = this.pos.get_order();
        if (order) {
            var pos_prod_id = order.selected_orderline.product.pos_categ_ids[0]
            if (this.pos.config.apply_discount_limit == false) {
                var parsed_discount =
                    typeof discount === "number" ?
                    discount :
                    isNaN(parseFloat(discount)) ?
                    0 :
                    oParseFloat("" + discount);
                var disc = Math.min(Math.max(parsed_discount || 0, 0), 100);
                this.discount = disc;
                this.discountStr = "" + disc;
            } else if (this.pos.config.apply_discount_limit == 'product_category') {
                var rounded = Math.round(discount);
                if (Number.isInteger(pos_prod_id)) {
                    if (this.pos.db.category_by_id[pos_prod_id].discount_limit) {
                        if (rounded > this.pos.db.category_by_id[pos_prod_id].discount_limit) {
                            this.pos.popup.add(ErrorPopup, {
                                'title': _t("Discount Not Possible"),
                                'body': _t("You cannot apply discount above the discount limit."),
                            });
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
            } else if (this.pos.config.apply_discount_limit == 'product') {
                var rounded = Math.round(discount);
                if (Number.isInteger(pos_prod_id)) {
                    if (this.get_product().product_discount_limit) {
                        if (rounded > this.get_product().product_discount_limit) {
                            this.pos.popup.add(ErrorPopup, {
                                'title': _t("Discount Not Possible"),
                                'body': _t("You cannot apply discount above the discount limit."),
                            });
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