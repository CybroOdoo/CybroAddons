/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ProductReviewScroll = publicWidget.Widget.extend({
    selector: '.oe_website_sale',
    events: {
        'click a[href="#o_product_page_reviews"]': '_onClickReviewsLink',
    },

    _onClickReviewsLink(ev) {
        ev.preventDefault();
        const reviewSection = document.querySelector('#o_product_page_reviews');
        const reviewContent = document.querySelector('#o_product_page_reviews_content');

        if (reviewSection) {
            reviewSection.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }

        if (reviewContent && reviewContent.classList.contains('collapse')) {
            reviewContent.classList.remove('collapse');
            reviewContent.classList.add('show');
        }
    },
});
