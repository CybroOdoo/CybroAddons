import { registry } from '@web/core/registry';
import { ShoppingCarousel } from '@theme_shopping/js/carousel';

class OfferSnippet extends ShoppingCarousel {
    static selector = '.offer_snippet';
    start() {
        this.setupCarousel(this.el.querySelector('#offer_product_carousel'), true);
    }
}
registry.category('public.interactions').add('theme_shopping.offer', OfferSnippet);
