/** @odoo-module */
import publicWidget from '@web/legacy/js/public/public_widget';
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.IndexAndFollow = publicWidget.Widget.extend({
     selector: '#product_detail_main',
     events: {
         'change .is_index': '_setProductIndex',
    },
    init() {
    this._super(...arguments);
    },
    async _setProductIndex(event){
//function to set product index
        var product = this.el.querySelector('.product').value;
        if (event.target.checked == true){
//   check index input is checked, if input is checked, it sends an request
//   to the server to set the product's indexing status to true.*/
            this.el.querySelector('.is_index').checked = true;
           await rpc('/web_index',{
                'index': true,
                'product': product,
            }).then(function(){
                 location.reload();
            });
        }
        else{
//                 input is unchecked, it sends an request to set the status to false.
             await rpc('/web_index',{
                'index': false,
                 'product': product,
             }).then(function(){
                 location.reload();
            });
        }
    },
});
