odoo.define('theme_eco_refine.collection_snippet', function(require) {
    "use strict";
    var publicWidget = require('web.public.widget');
    /**
     * Widget for displaying Collection snippet.
     */
    publicWidget.registry.collection_snippet = publicWidget.Widget.extend({
        selector: '.ref-collection--container',
        start: function() {
            var self = this;
            return this._super.apply(this, arguments).then(async function() {
                const items = document.querySelectorAll('.ref-collection__item');
                items.forEach((item, index) => {
                    if (index === 0) {
                        item.classList.add('selected');
                    }
                    item.addEventListener('click', () => {
                        items.forEach(item => item.classList.remove('selected'));
                        item.classList.add('selected');
                    });
                });

            });
        },
    });
    return publicWidget.registry.collection_snippet;
})
