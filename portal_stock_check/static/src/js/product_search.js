/** @odoo-module **/
import { renderToElement } from "@web/core/utils/render";
import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";
/**
 * Widget PortalHomeCountersProduct
 *
 * Display the search tab
 *
 */
export const PortalHomeCountersProduct = publicWidget.Widget.extend({
    selector: '.o_website_product_search',
    events:{
    'keyup .o_portal_product_input': '_product_search',
    },
       /**
     * @constructor
     */
    init() {
        this._super(...arguments);
    },
        /**
     * @private
     * Display  table of product and quantity available using jsonrpc call
     */
    async _product_search(result){
     var product_name = $('#product_name_input').val();
      await jsonrpc('/product/search', {
      args: {'product':product_name}
                }).then(function(result){
                 if (result != 'false'){
                 }
                 $('.product_results_table').html(renderToElement('productSearch',
                 {
                 result:result
                 }));
                })
    }
    })
publicWidget.registry.PortalHomeCountersProduct = PortalHomeCountersProduct;
