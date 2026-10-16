import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';

class ProductReviewScroll extends Interaction {
    static selector = '.oe_website_sale';
    dynamicContent = {
        'a[href="#o_product_page_reviews"]': { 't-on-click.prevent': this.showReviews },
    };
    showReviews() {
        const section = document.querySelector('#o_product_page_reviews');
        const content = document.querySelector('#o_product_page_reviews_content');
        content?.classList.add('show');
        section?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}
registry.category('public.interactions').add('theme_shopping.reviews', ProductReviewScroll);
