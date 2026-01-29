odoo.define('website_return_management.return', function(require) {
    "use strict";
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var QWeb = core.qweb;
    /**
        new component to publicWidget
     */
    publicWidget.registry.returnOrderModal = publicWidget.Widget.extend({
        selector: 'div[id="sale_return_modal"]',
        events: {
            'click #hidden_box_btn': '_onShowButtonClick',
            'change #product': '_onShowFormSubmit',
            'click #submit': '_onClickFormSubmit',
            'change #qty': '_onChangeQuantity',
        },
        _onShowButtonClick: function() {
            /**
            on-click function to show the modal
            */
            $('#hidden_box').modal('show');
        },
        _onShowFormSubmit: function() {
            /**
            on-click function to show the submit button
            */
            var x = $('#submit');
            x.addClass('d-none');
            if ($("#product").val() == 'none') {
                if (!x.hasClass('d-none')) {
                    x.addClass('d-none');
                }
            } else {
                if (x.hasClass('d-none')) {
                    x.removeClass('d-none');
                }
            }
        },

        _onChangeQuantity: function() {
         /**
           on-change function to check the quantity
         */
         if (!$("#warning_message").hasClass('d-none')) {
    $('#warning_message').addClass('d-none');
    $('#submit').prop('disabled', false);
}
    else if (!$("#product_null_warning").hasClass('d-none')){
              $('#product_null_warning').addClass('d-none');
         $('#submit').prop('disabled', false);
         }
        },

        _onClickFormSubmit: function(ev) {
            /**
            on-click function to show the submit button
            */
            ev.preventDefault();
            var current_order = $('#order_id').val()
            var return_qty = $('#qty').val()
            var product = $('#product').val()
            var reason = $('#return_reason').val()
            ajax.jsonRpc('/order_quantity', 'call', {
            'current_order': current_order, 'return_qty': return_qty,
            'product_id': product})
                .then(function(data) {
                       if (data < return_qty) {
                         $('#warning_message').removeClass('d-none');
                    }
                     else if (return_qty <= 0){
                      $('#product_null_warning').removeClass('d-none');
                      $('#submit').prop('disabled', true);
                     }
                     else {
                          // Submit the form if the condition is met
                          ajax.jsonRpc('/sale_return', 'call', {
                          'order_id': current_order, 'qty': return_qty,
                          'product': product, 'reason': reason}).then(function(result) {
                           window.location.href = '/my/request-thank-you';
                          })
                    }
                    });

        },
    })
})
