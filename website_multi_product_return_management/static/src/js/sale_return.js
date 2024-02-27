/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { useService } from "@web/core/utils/hooks";

publicWidget.registry.ReturnForm = publicWidget.Widget.extend({
    selector: '.sale_return',
    // Event handlers for specific actions
    events:{
    'click #hidden_box_btn': '_showModal',
    'click .js_add_json': '_validation',
    'submit .sale_return_form': '_submission',
    },
    init: function () {
        this._super.apply(this, arguments);
                this.rpc = this.bindService("rpc");
    },
    start: async function () {
        await this._super(...arguments);
    },
    // Show modal when #hidden_box_btn is clicked
    _showModal: function () {
                            $('#hidden_box').modal('show');
    },
    // Validate quantity based on user interaction
    _validation: function (ev) {
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
    },
    // Handle form submission
    _submission: async function (submission) {
            submission.preventDefault();
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
        await this.rpc("/sale_return", {
            'vals': val,
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
    },
});
