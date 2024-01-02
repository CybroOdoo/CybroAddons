odoo.define('featured_brand_snippet.s_dynamic_brand', function(require) {
    'use strict';

    const core = require('web.core');
    const publicWidget = require('web.public.widget');
    const rpc = require('web.rpc');
    const qweb = core.qweb;
    var ajax = require('web.ajax');

    const ProductBrandDynamic = publicWidget.Widget.extend({
        selector: '.dynamic_snippet_brand',
        xmlDependencies: ['/featured_brand_snippet/static/src/xml/dynamic_brand_carousel.xml'],
/**Calling the route for returning the brands name, image &ID*/
        willStart: async function() {
            var self = this;
            await rpc.query({
                route: '/product_brand',
            }).then((data) => {
                this.data = data;
            });
            var proms = [];
            if (this.xmlDependencies) {
                proms.push.apply(proms, _.map(this.xmlDependencies, function(xmlPath) {
                    return ajax.loadXML(xmlPath, core.qweb);
                }));
            }
            return Promise.all(proms);
        },
/** chunkArray is an alternative to chunk*/
        chunkArray: function(array, chunkSize) {
            var result = [];
            for (var i = 0; i < array.length; i += chunkSize) {
                var chunk = array.slice(i, i + chunkSize);
                result.push(chunk);
            }
            return result;
        },
/**For calling the brand snippet template*/
        start: function() {
            var chunks = this.chunkArray(this.data, 4)
            if (!chunks.length == 0) {
            chunks[0].is_active = true;
            this.$el.find('#brands').html(
                core.qweb.render('brand_snippet_carousel', {
                    chunks
                })
            )
          }
        },
    });
    publicWidget.registry.featured_brand_snippet = ProductBrandDynamic;
    return ProductBrandDynamic;
});