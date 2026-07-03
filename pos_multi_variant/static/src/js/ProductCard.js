/** @odoo-module **/

import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";

/**
 * Add isPosVariants prop to ProductCard so label.xml can use it.
 * We patch the static props directly since patch() is designed for prototype methods.
 */
ProductCard.props = {
    ...ProductCard.props,
    isPosVariants: { type: Boolean, optional: true },
};
