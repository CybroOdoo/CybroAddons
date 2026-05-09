/** @odoo-module */

import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";

/**
 * Add the isMealPlanProduct prop so Owl doesn't throw a validation error
 * when the ProductScreen XML passes this attribute to ProductCard.
 */
ProductCard.props.isMealPlanProduct = { type: Boolean, optional: true };
