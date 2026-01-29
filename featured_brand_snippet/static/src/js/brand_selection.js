/** @odoo-module **/

import core from 'web.core';
import publicWidget from 'web.public.widget';
import rpc from 'web.rpc';
import ajax from 'web.ajax';
var qweb = core.qweb;

const ProductBrandDynamic = publicWidget.Widget.extend({
    selector: '.dynamic_snippet_brand',
    xmlDependencies: ['/featured_brand_snippet/static/src/xml/dynamic_brand_carousel.xml'],

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
        var proms = [];
        //ajax loading qweb template
        if (this.xmlDependencies) {
            proms.push.apply(proms, _.map(this.xmlDependencies, function(xmlPath) {
                return ajax.loadXML(xmlPath, core.qweb);
            }));
        }
        return Promise.all(proms);
    },
    /**
    chunkArray is an alternative to chunk
    */
    chunkArray: function(array, chunkSize) {
        var result = [];
        for (var i = 0; i < array.length; i += chunkSize) {
            var chunk = array.slice(i, i + chunkSize);
            result.push(chunk);
        }
        return result;
    },

    /**
    For calling the brand snippet template
    */
    start: function() {
        var chunks = this.chunkArray(this.data, 4)
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