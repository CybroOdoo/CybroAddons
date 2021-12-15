//odoo.define('theme_boec.price_filter', function (require) {
//	"use strict";
//
//	$(document).on("click", "#products_grid_before .price_filter_button", function(event){
//        event.preventDefault();
//
//        var amounts = $("#amount").val().split("-");
//        var min = amounts[0];
//        var max = amounts[1];
//        var max_amount = $("#boec_max_price").val();
//
//        if ((min == max_amount) && (max == max_amount)) {
//          $('#minimum').val(amounts[0]);
//          $('#maximum').val(amounts[1]);
//        } else if (min == max_amount){
//          $('#minimum').val(0);
//          $('#maximum').val(max_amount);
//        } else {
//          $('#minimum').val(amounts[0]);
//          $('#maximum').val(amounts[1]);
//        }
//
//        $("#products_grid_before form.js_attributes").submit();
//    });
//})
