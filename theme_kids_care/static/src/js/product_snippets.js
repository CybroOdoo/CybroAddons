/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

/**
 * Product Snippets Widget for Kids Care theme.
 * Handles attribute selection (size, color) within various product-related
 * sections and snippets on the website.
 */
publicWidget.registry.KidsCareProductSnippets = publicWidget.Widget.extend({
    selector: '.o_wsale_products_page, .section-tab, .section-all-the-snekers, .section-best-sellers, .section-skincare-products',
    events: {
        'click .badge-attr-select': '_onSizeClick',
        'click .color-attr-select': '_onColorClick',
        'click .size-1, .size-2': '_onSnippetSizeClick',
    },
    /**
     * Handles size attribute selection in product pages/snippets.
     * @private
     * @param {Event} ev
     */
    _onSizeClick: function (ev) {
        const $el = $(ev.currentTarget);
        $el.siblings('.badge-attr-select').removeClass('active bg-primary text-white');
        $el.addClass('active');
        // In a real scenario, this would update the product_id hidden input
    },
    /**
     * Handles color attribute selection in product snippets.
     * @private
     * @param {Event} ev
     */
    _onColorClick: function (ev) {
        const $el = $(ev.currentTarget);
        $el.siblings('.color-attr-select').removeClass('active');
        $el.addClass('active');
    },
    /**
     * Handles specific snippet size selector clicks.
     * @private
     * @param {Event} ev
     */
    _onSnippetSizeClick: function (ev) {
        const $el = $(ev.currentTarget);
        $el.siblings().removeClass('active1');
        $el.addClass('active1');
    },
});

export default publicWidget.registry.KidsCareProductSnippets;
