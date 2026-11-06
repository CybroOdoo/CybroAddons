/** @odoo-module **/

import { registry } from "@web/core/registry";
import * as tourUtils from "@website_sale/js/tours/tour_utils";

registry.category("web_tour.tours").add('website_purchase_limit_test_below', {
    url: '/shop',
    steps: () => [
        ...tourUtils.searchProduct("Limit Product Below", { select: true }),
        {
            content: "click on add to cart",
            trigger: '#add_to_cart',
            run: "click",
        },
        tourUtils.goToCart({quantity: 1}),
        {
            content: "Check if limit div is present",
            trigger: '#website_purchase_limit_value:not(:visible)',
        },
        {
            content: "Click checkout",
            trigger: 'a[name="website_sale_main_button"]',
            run: "click",
        },
        {
            content: "Check popup is present",
            trigger: '#popup_error_message',
        }
    ]
});

registry.category("web_tour.tours").add('website_purchase_limit_test_above', {
    url: '/shop',
    steps: () => [
        ...tourUtils.searchProduct("Limit Product Above", { select: true }),
        {
            content: "click on add to cart",
            trigger: '#add_to_cart',
            run: "click",
        },
        tourUtils.goToCart({quantity: 1}),
        {
            content: "Check if limit div is NOT present",
            trigger: 'body:not(:has(#website_purchase_limit_value))',
        },
        tourUtils.goToCheckout(),
    ]
});

registry.category("web_tour.tours").add('website_purchase_limit_test_disabled', {
    url: '/shop',
    steps: () => [
        ...tourUtils.searchProduct("Limit Product Below", { select: true }),
        {
            content: "click on add to cart",
            trigger: '#add_to_cart',
            run: "click",
        },
        tourUtils.goToCart({quantity: 1}),
        {
            content: "Check if limit div is NOT present",
            trigger: 'body:not(:has(#website_purchase_limit_value))',
        },
        tourUtils.goToCheckout(),
    ]
});

registry.category("web_tour.tours").add('website_purchase_limit_test_exact', {
    url: '/shop',
    steps: () => [
        ...tourUtils.searchProduct("Limit Product Exact", { select: true }),
        {
            content: "click on add to cart",
            trigger: '#add_to_cart',
            run: "click",
        },
        tourUtils.goToCart({quantity: 1}),
        {
            content: "Check if limit div is NOT present",
            trigger: 'body:not(:has(#website_purchase_limit_value))',
        },
        tourUtils.goToCheckout(),
    ]
});
