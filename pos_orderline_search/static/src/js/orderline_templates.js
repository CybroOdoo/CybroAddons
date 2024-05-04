/** @odoo-module **/
import { OrderWidget } from "@point_of_sale/app/generic_components/order_widget/order_widget";
import { patch } from "@web/core/utils/patch";
import { useRef, useState } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
// Patch the OrderSummary to add custom properties
patch(OrderWidget.prototype, {
    setup(...args) {
        super.setup(...args);
        this.state = useState({
            search_line: [],
            productInLine: false,
            search: "",
        });
    },
    /**
     * Get the event items in the input search.
     *
     * @returns [product] The items in the orderline.
     */
    _keyup(event) {
        let SearchProduct = event.currentTarget.value.toLowerCase();
        let orderLine = this.env.services.pos.selectedOrder.orderlines;
        if (orderLine.length !=0){
            if (SearchProduct && SearchProduct.length > 0) {
                let MatchingLines = orderLine.filter(function(line) {
                let product = line.get_product();
                return product.display_name.toLowerCase().includes(SearchProduct);
            });
            this.state.search_line = MatchingLines
            if (MatchingLines.length == 0){
             this.state.productInLine = true;
            }
            else{
                this.state.productInLine = false;
            }
            }
        }
    },
    /**
     * Clear the search input.
     */
    _keyPress(line){
        line.pos.orders[0].orderlines.forEach(function(line) {
            line.set_selected(false)
        });
        line.set_selected(true)
    },
    _OnclickCancelSearch(event){
        this.state.search = "";
    },
});
OrderWidget.components = {...OrderWidget.components, Dropdown, DropdownItem}
