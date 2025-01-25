import { WebsiteSale } from "@website_sale/js/website_sale";
import { patch } from "@web/core/utils/patch";

patch(WebsiteSale.prototype, {
     _onClickReviewsLink() {
        const reviewSection = document.querySelector('#o_product_page_reviews');
        const reviewContent = document.querySelector('#o_product_page_reviews_content');

        reviewSection.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });

        if (reviewContent.classList.contains('collapse')) {
            reviewContent.classList.remove('collapse');
            reviewContent.classList.add('show');
        }
    },

});
