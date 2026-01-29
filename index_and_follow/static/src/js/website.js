odoo.define('index_and_follow.index', function (require) {
'use strict';
    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');
    publicWidget.registry.IndexAndFollow = publicWidget.Widget.extend({
         selector: '#product_details',
         events: {
             'change .is_index': '_setProductIndex',
        },
        _setProductIndex: function(event){
            //function to set product index
            var product = this.el.querySelector('.product').value;
            if (event.target.checked == true){
                /*check index input is checked, if input is checked, it sends an AJAX request
                 to the server to set the product's indexing status to true.*/
                this.el.querySelector('.is_index').checked = true;
                ajax.jsonRpc('/web_index', 'call',{
                    'index': true,
                    'product': product,
                }).then(function(){
                     window.location.reload();
                });
            }
            else{
                 //input is unchecked, it sends an AJAX request to set the status to false.
                 ajax.jsonRpc('/web_index', 'call',{
                    'index': false,
                     'product': product,
                 }).then(function(){
                     window.location.reload();
                });
            }
        },
    });
    return publicWidget.registry.IndexAndFollow;
  });
