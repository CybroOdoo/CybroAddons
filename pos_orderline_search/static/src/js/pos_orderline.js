odoo.define('pos_orderline_search.pos_orderline', function (require) {
    'use strict';
    const OrderWidget = require('point_of_sale.OrderWidget');
    /**
     * Override the _keyup method of OrderWidget to perform search functionality.
     * event - The keyup event object.
     */
    OrderWidget.prototype._keyup = function(event) {
        var SearchProduct = event.currentTarget.value.toLowerCase();
        var orderLine =  this.env.pos.get_order().orderlines;
        var div = this.el.querySelectorAll(".orderline-product-list");
        $(div).empty();
        div[0].style.display = 'none'
        if (SearchProduct && SearchProduct.length > 0) {
            div[0].style.display = 'block'
            var MatchingLines = orderLine.filter(function(line) {
                var product = line.get_product();
                return product.display_name.toLowerCase().includes(SearchProduct);
            });
            MatchingLines.forEach(function(line) {
                var $link = $("<a class='search-products' autofocus='autofocus' href='#" + line.id + "' id='" + line.id + "'>").text(line.get_full_product_name());
                var $li = $("<li>").append($link);
                $(div).append($li);
            });
        }
    };
    /**
     * Override the _keyPress method of OrderWidget to handle line selection.
     * event - The keypress event object.
     */
    OrderWidget.prototype._keyPress = function(event) {
        var searchBar = this.el.querySelectorAll(".search-product")
         if (event.target.text){
            var orderLines =  this.env.pos.get_order().orderlines;
            searchBar[0].value=event.target.text
            orderLines.forEach(function(line) {
                $("#"+line.id+"")[0].classList.remove("selected");
                line.selected = false;
                if (line.id == event.target.id) {
                    console.log($("#"+line.id+""))
                    $("#"+line.id+"")[0].classList.add("selected");
                    line.selected = true;
                }
            });
        }else{
              searchBar[0].value="";
              this.el.querySelectorAll(".orderline-product-list")[0].style.display="none"
        }
    };
});
