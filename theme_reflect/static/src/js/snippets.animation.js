/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ReflectCategoryGrid = publicWidget.Widget.extend({
    selector: '.s_reflect_category_grid',
    disabledInEditableMode: true,

    init(root, options) {
        const parent = options.parent || root;
        this._super(parent, options);
        this.rpc = this.bindService("rpc");
    },

    start: function () {
        this._super.apply(this, arguments);
        this._loadCategories();
    },

    _loadCategories: function () {
        this.rpc('/theme_reflect/get_categories', {})
            .then((data) => {
                if (data) {
                    this.$target.find('.reflect-cat-grid-container').html(data);
                }
            });
    },
});

publicWidget.registry.ReflectNewArrivals = publicWidget.Widget.extend({
    selector: '.s_reflect_new_arrivals',
    disabledInEditableMode: true,

    init(root, options) {
        const parent = options.parent || root;
        this._super(parent, options);
        this.rpc = this.bindService("rpc");
    },

    start: function () {
        this._super.apply(this, arguments);
        this._loadProducts();
    },

    _loadProducts: function () {
        this.rpc('/theme_reflect/get_new_arrivals', {})
            .then((data) => {
                if (data) {
                    this.$target.find('.reflect-new-arrivals-container').html(data);
                }
            });
    },
});

publicWidget.registry.ReflectProductHighlight = publicWidget.Widget.extend({
    selector: '.s_reflect_product_highlight',
    disabledInEditableMode: true,

    init(root, options) {
        const parent = options.parent || root;
        this._super(parent, options);
        this.rpc = this.bindService("rpc");
    },

    start: function () {
        this._super.apply(this, arguments);
        this._loadProducts();
    },

    _loadProducts: function () {
        this.rpc('/theme_reflect/get_product_highlight', {})
            .then((data) => {
                if (data) {
                    this.$target.find('.reflect-product-highlight-container').html(data);
                }
            });
    },
});
