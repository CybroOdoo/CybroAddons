/** @odoo-module */
import publicWidget from '@web/legacy/js/public/public_widget';
import { jsonrpc } from "@web/core/network/rpc_service";
    publicWidget.registry.IndexAndFollow = publicWidget.Widget.extend({
         selector: '#product_detail_main',
         events: {
             'change .is_index': '_setProductIndex',
        },
        init() {
        this._super(...arguments);
        },
        async _setProductIndex(event){
//            //function to set product index
            var product = this.el.querySelector('.product').value;
            if (event.target.checked == true){
            console.log("event.target.checked",event.target.checked)
//   check index input is checked, if input is checked, it sends an request
//   to the server to set the product's indexing status to true.*/
                this.el.querySelector('.is_index').checked = true;
               await jsonrpc('/web_index',{
                    'index': true,
                    'product': product,
                }).then(function(){
                     location.reload();
                });
            }
            else{
//                 input is unchecked, it sends an request to set the status to false.
                 await jsonrpc('/web_index',{
                    'index': false,
                     'product': product,
                 }).then(function(){
                     location.reload();
                });
            }
        },
    });
