/** @odoo-module */

import { Component } from "@odoo/owl";
import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { patch } from "@web/core/utils/patch";

//Patched the ProductCard for defining that clickMagnifyProduct is function
patch(ProductCard.prototype, {
    //Supering setup() function
    setup() {
        super.setup();
    },
});
ProductCard.props = {
    clickMagnifyProduct: {
        type: Function,
        optional: true
    },
};
ProductCard.defaultProps = {
    onClick: () => {},
    class: "",
};
