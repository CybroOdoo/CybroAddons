/** @odoo-module **/
import { OrderDisplay } from "@point_of_sale/app/components/order_display/order_display";
import { patch } from "@web/core/utils/patch";
import { useRef, useState } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
// Patch the OrderSummary to add custom properties
patch(OrderDisplay.prototype, {
    setup(...args) {
        super.setup(...args);
        var self = this
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
        let SearchProduct = event.target.value.toLowerCase();
        let orderLine = this.props.order.lines;
        if (orderLine.length !=0){
            if (SearchProduct && SearchProduct.length > 0) {
                let MatchingLines = orderLine.filter(function(line) {
                let product = line.getProduct();
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
        line.set_selected = false
    },
    _OnclickCancelSearch(event){
        this.state.search = "";
    },
});
OrderDisplay.components = {...OrderDisplay.components, Dropdown, DropdownItem}
