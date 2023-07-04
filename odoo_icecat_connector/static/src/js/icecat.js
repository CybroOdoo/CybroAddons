odoo.define('odoo_icecat_connector.icecat_products', function(require) {
    'use strict';
    // Calling the method to get the product details from the icecat db and pass
    //the corresponding details to the website
    var rpc = require('web.rpc')
    rpc.query({
        model: 'product.template',
        method: 'get_icecat_product_details',
        args: [
            [], $('.product_id').val()
        ],
    }).then(function(data) {
        if (data) {
            if (data.brand != false) {
                IcecatLive.getDatasheet({
                    'title': '#icecat_title',
                    'essentialinfo': '#icecat_essentialinfo',
                    'marketingtext': '#icecat_marketingtext',
                    'manuals': '#icecat_manuals',
                    'reasonstobuy': '#icecat_reasonstobuy',
                    'reviews': '#icecat_reviews',
                    'featuregroups': '#icecat_featuregroups',
                    'gallery': '#icecat_gallery',
                    'featurelogos': '#icecat_featurelogos',
                    'tours3d': '#icecat_tours3d',
                    'videos': '#icecat_videos',
                    'productstory': '#icecat_productstory'
                }, {
                    Brand: data.brand,
                    PartCode: data.product_code,
                    UserName: data.username,
                }, 'en')
            }
        }
    });
});