/** @odoo-module **/
import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';

export class ProductGallery extends Interaction {
    static selector = '.pd-gallery';
    dynamicContent = {
        '.pd-thumb': { 't-on-click': this.onThumbClick },
    };

    onThumbClick(ev) {
        const thumb = ev.currentTarget;
        const src = thumb.dataset.src;
        const mainImg = this.el.querySelector('.pd-main img');
        if (!src || !mainImg) {
            return;
        }
        mainImg.src = src;
        mainImg.removeAttribute('srcset');
        this.el.querySelectorAll('.pd-thumb').forEach(
            (t) => t.classList.toggle('active', t === thumb)
        );
    }
}

registry.category('public.interactions').add('theme_beauty_shop.product_gallery', ProductGallery);