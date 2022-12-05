odoo.define('theme_xtream.price_filter', function (require) {
	"use strict";

    $(document).on("click", "#products_grid_before .price_filter_button", function(event){
        event.preventDefault();

        var amounts = $("#amount").val().split("-");
        var min = amounts[0];
        var max = amounts[1];
        var max_amount = 100000;

        if ((min == max_amount) && (max == max_amount)) {
          var minimum = $('#minimum').val(amounts[0]);
          var maximum = $('#maximum').val(amounts[1]);
        } else if (min == max_amount){
          var minimum = $('#minimum').val(0);
          var maximum = $('#maximum').val(max_amount);
        } else {
          var minimum = $('#minimum').val(amounts[0]);
          var maximum = $('#maximum').val(amounts[1]);
        }

        $("#products_grid_before form.js_attributes").submit();
    });
})
