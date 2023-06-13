odoo.define('featured_brand_snippet.s_dynamic_brand', function(require) {
    'use strict';

    const core = require('web.core');
    const publicWidget = require('web.public.widget');
    const rpc = require('web.rpc');
    const qweb = core.qweb;

    const ProductBrandDynamic = publicWidget.Widget.extend({
        selector: '.dynamic_snippet_brand',

        /**
        Calling the route for returning the brands name, image &ID
        */
        willStart: async function() {
            var self = this;
            await rpc.query({
                route: '/product_brand',
            }).then((data) => {
                this.data = data;
            });
        },

        /**
        For calling the brand snippet template
        */
        start: function() {
            var chunks = _.chunk(this.data, 4)
            if (!chunks.length == 0) {
                chunks[0].is_active = true;
                this.$el.find('#brands').html(
                    qweb.render('featured_brand_snippet.brand_snippet_carousel', {
                        chunks
                    })
                )
            }

        },
    });

    publicWidget.registry.featured_brand_snippet = ProductBrandDynamic;

    return ProductBrandDynamic;
});