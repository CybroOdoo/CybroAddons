odoo.define('website_multi_product_return_management.return', function (require) {
    "use strict";

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');

    $("#hidden_box_btn").on('click', function () {
        $('#hidden_box').modal('show');

    })
    $(".js_add_json").on('click', function (ev) {
        var $link = $(ev.currentTarget);
        var $input = $link.closest('.input-group').find("input");
        var min = parseFloat($input.data("min") || 0);
        var max = parseFloat($input.data("max") || Infinity);
        var previousQty = parseFloat($input.val() || 0, 10);
        var quantity = ($link.has(".fa-minus").length ? -1 : 1) + previousQty;
        var newQty = quantity > min ? (quantity < max ? quantity : max) : min;
        if (newQty !== previousQty) {
            $input.val(newQty).trigger('change');
        }
        return false;
    })

    $('#sale_return_form').on('submit', function(submission) {
        var val = []
        submission.preventDefault();

        $("tr.order_line").each(function() {
        var qty = parseFloat($(this).find(".quantity").val() || 0);
            if (qty !== 0){
                    val.push({ 'order_id' : $(this).find(".quantity").data("order-id"),
                        'line_id' : $(this).find(".quantity").data("line-id"),
                        'deli_qty' : $(this).find(".quantity").data("delivered_qty"),
                         'quantity' : $(this).find(".quantity").val(),
                         'product_id' : $(this).find(".quantity").data('product-id'),
                         'reason' : $(this).find("#return_reason").val()});
                }
        });

        if (val.length !== 0){
            ajax.jsonRpc('/sale_return', 'call', {
                        'vals':val,
            }).then(function(result){
                if (result == true){

                  window.location.href = '/my/request-thank-you';

                }
                else{
                    alert("Retry again");
                }
            });
        }
        else{
            alert("Please specify at least one return quantity");
            submission.preventDefault();
        }
    });

});