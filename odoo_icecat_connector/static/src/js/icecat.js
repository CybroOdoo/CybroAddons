/** @odoo-module **/

import { jsonrpc } from "@web/core/network/rpc_service";

/**
 * Fetches Icecat product details based on the provided product ID.
 */
function fetchIcecatProductDetails() {
    // Get the product ID from the element with the class 'product_id'
    var product_id = $('.product_id').val();
    // Check if the product ID is defined
    if (typeof $('.product_id').val() !== "undefined") {
        // Make a JSON-RPC call to retrieve Icecat product details
        jsonrpc('/get_icecat_product_details', {
            'product_id': $('.product_id').val(),
        }).then((data) => {
            if (data.status) {
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
                    }, 'en');
            }
        });
    }
}
// Call the function to fetch Icecat product details
fetchIcecatProductDetails();
