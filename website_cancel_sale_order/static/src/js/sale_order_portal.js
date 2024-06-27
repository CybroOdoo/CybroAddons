/** @odoo-module **/
//This JavaScript function handles the cancellation of a sale order on the website.
//The function checking for there is a valid reason for cancelling the order
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
publicWidget.registry.WebsiteSaleOrderCancel = publicWidget.Widget.extend({
     selector: '.editReasonForm',
     events: {
            'click #submit_button': '_onSubmit',
        },
        _onSubmit: function (e) {
            var reason = this.$("#reason").val();
            var sale_order_id =this.$("#sale_order_id").val();
            var iChars = /[`!@#$%^&*()_+\-=\[\]{}]/;
            var iCharsString = iChars.toString().slice(1, -1);
            var numbers=/[^0-9]/;
            var containsSpecialChars = new RegExp('[' + iCharsString.replace(/([()[\]{}\-.*+?^$|\\])/g, '\\$1') + ']').test(reason); // Convert regex to string
             if (reason == "" || containsSpecialChars || !numbers.test(reason) ) {
                    alert("Please specify the reason properly");
                    e.preventDefault();
                }
             else{
                  jsonrpc("/cancel/reason/edit", {
                       'reason': reason,
                       'sale_order_id': sale_order_id
                  })
                  .then(function() {
                     location.reload();
            });
            }
        }
    });
    var WebsiteSaleOrderCancel = new publicWidget.registry.WebsiteSaleOrderCancel(this);
    WebsiteSaleOrderCancel.appendTo($(".editReasonForm"));
    return publicWidget.registry.WebsiteSaleOrderCancel;
