/** @odoo-module **/
import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import { rpc } from '@web/core/network/rpc';

export class IndexAndFollow extends Interaction {
    static selector = '#product_detail_main';
    dynamicContent = {
        '.is_index': { 't-on-change': this._setProductIndex },
    };

    async _setProductIndex(ev) {
        const wrap = ev.target.closest('#product_detail_main') || this.el;
        const productInput = wrap.querySelector('.product');
        const product = productInput ? productInput.value : null;
        if (!product) {
            return;
        }
        await rpc('/web_index', {
            index: ev.target.checked,
            product: product,
        });
        window.location.reload();
    }
}

registry
    .category('public.interactions')
    .add('index_and_follow.index_and_follow', IndexAndFollow);

// Fallback event listener for direct DOM change
document.addEventListener('change', async (ev) => {
    if (ev.target && ev.target.classList.contains('is_index')) {
        const wrap = ev.target.closest('#product_detail_main') || document;
        const productInput = wrap.querySelector('.product');
        const product = productInput ? productInput.value : null;
        if (product) {
            await rpc('/web_index', {
                index: ev.target.checked,
                product: product,
            });
            window.location.reload();
        }
    }
});
