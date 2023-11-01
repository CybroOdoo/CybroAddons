odoo.define('pos_orderline_search.pos_orderline.js', function (require) {
    'use strict';
    const OrderWidget = require('point_of_sale.OrderWidget');
    /**
     * Override the _keyup method of OrderWidget to perform search functionality.
     * event - The keyup event object.
     */
    OrderWidget.prototype._keyup = function(event) {
        var SearchProduct = event.currentTarget.value.toLowerCase();
        var orderLine = this.env.pos.selectedOrder.orderlines;
        var orderline_product_list = $(this.__owl__.bdom.refs[6])
        var no_product_warning = $(this.__owl__.bdom.refs[6].nextElementSibling)
        orderline_product_list.empty()
        if (orderLine.length !=0){
        if (SearchProduct && SearchProduct.length > 0) {
            var MatchingLines = orderLine.filter(function(line) {
                var product = line.get_product();
                return product.display_name.toLowerCase().includes(SearchProduct);
            });

            MatchingLines.forEach(function(line) {
                var $link = $("<a class='search-products' autofocus='autofocus' href='#" + line.id + "' id='" + line.id + "'>").text(line.get_full_product_name());
                var $li = $("<li>").append($link);
               orderline_product_list.append($li);
            });
           if (MatchingLines.length == 0){

             no_product_warning.show();
             orderline_product_list.hide();
           }
           else{
                 no_product_warning.hide();
                 orderline_product_list.show();
           }
        }
        if (!SearchProduct){
         no_product_warning.hide();
         orderline_product_list.hide();
        }
        }
    };
    /**
     * This function works when we click on the close button.
     */
    OrderWidget.prototype._OnclickCancelSearch = function(event) {
        $(this.__owl__.bdom.refs[4]).val('');//replace the searchbar empty
        $(this.__owl__.bdom.refs[6].nextElementSibling).hide();
        $(this.__owl__.bdom.refs[6]).empty();
        $(this.__owl__.bdom.refs[6]).hide();
    }
    /**
     * Override the _keyPress method of OrderWidget to handle line selection.
     * event - The keypress event object.
     */
    OrderWidget.prototype._keyPress = function(event) {
        var orderLines = this.env.pos.selectedOrder.orderlines;
        orderLines.forEach(function(line) {
            line.selected = false;
            if (line.id == event.target.id) {
                line.selected = true;
            }
        });
    };
});
