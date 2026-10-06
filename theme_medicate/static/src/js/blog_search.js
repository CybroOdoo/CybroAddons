/** @odoo-module **/

import PublicWidget from "@web/legacy/js/public/public_widget";

PublicWidget.registry.ProductInfoWidget = PublicWidget.Widget.extend({
    selector: '#blog_search_form, .blog_search_form, .blog-search-container form',
    events: {
        'submit': '_onBlogInfoClick',
    },

    _onBlogInfoClick: function(ev) {
        ev.preventDefault();
        const $form = $(ev.currentTarget);
        const query = ($form.find('input[name="search"]').val() || '').trim();

        if (!query) {
            window.location.href = '/blog';
            return;
        }

        window.location.href = '/blog?search=' + encodeURIComponent(query);
    },
});
