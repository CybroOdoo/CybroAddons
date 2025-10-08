/**@odoo-module*/
var publicWidget = require('web.public.widget');
import rpc from 'web.rpc';
publicWidget.registry.WarrantyClaim = publicWidget.Widget.extend({
    selector: '.container',
    events: {
        'click #customer_id': '_onClickCustomer',
        'click #sale_order_id': '_onClickSaleOrder',
        'submit #form_submit': '_onSubmit'
    },
    _onClickCustomer: function (ev) {
    //    To show the sale order of the selected customer only
        ev.preventDefault();
        var selectedCustomerId = this.$('#customer_id').val();
         var $saleOrderDropdown = this.$('#sale_order_id');
        var $productDropdown = this.$('#products_id');
        $saleOrderDropdown.empty().append('<option value="">Select Sale Order</option>').prop('disabled', true);
        $productDropdown.empty().append('<option value="">Select Product</option>').prop('disabled', true);
        if (selectedCustomerId) {
            rpc.query({
                model: 'sale.order',
                method: 'search_read',
                args: [
                    [['partner_id', '=', parseInt(selectedCustomerId)]],  // Apply domain condition
                    ['name'],
                ],
            }).then(function (result) {
               if (result.length > 0) {
                $saleOrderDropdown.prop('disabled', false);
                $.each(result, function (i, saleOrder) {
                    $saleOrderDropdown.append($('<option>', {
                        value: saleOrder.id,
                        text: saleOrder.name,
                    }));
                });
                $productDropdown.prop('disabled', false);
            } else {
                $productDropdown.prop('disabled', true);
            }
        });
    }
},
    _onClickSaleOrder: function (ev) {
        ev.preventDefault();
        var selectedSaleOrderId = $('#sale_order_id').val();
        var $productDropdown = this.$('#products_id');
        $productDropdown.empty().append('<option value="">Select Product</option>').prop('disabled', true);
        if (selectedSaleOrderId) {
            rpc.query({
                model: 'sale.order.line',
                method: 'search_read',
                args: [
                    [['order_id', '=', parseInt(selectedSaleOrderId)]],
                    ['product_id'],
                ],
            }).then(function (result) {
                var $productDropdown = $('#products_id');
                $productDropdown.prop('disabled', false);
                $productDropdown.empty();
                $.each(result, function (i, saleOrderLine) {
                    $productDropdown.append($('<option>', {
                        value: saleOrderLine.product_id[0],
                        text: saleOrderLine.product_id[1],
                    }));
                });
            });
        }
    },
    _onSubmit: function (ev) {
        ev.preventDefault();
        // Get the selected sale order ID, customer ID, and product ID
        var selectedSaleOrderId = $('#sale_order_id').val();
        var selectedCustomerId = $('#customer_id').val();
        var selectedProductId = $('#products_id').val();
        var errorMessageElement = $('#error_message');
        if (selectedSaleOrderId && selectedCustomerId && selectedProductId) {
            rpc.query({
                model: 'warranty.claim',
                method: 'search_count',
                args: [
                    [['sale_order_id', '=', parseInt(selectedSaleOrderId)]],
                ],
            }).then(function (count) {
                if (count > 0) {
                    errorMessageElement.text("A warranty claim for this sale order already exists.");
                    setTimeout(function () {
                        errorMessageElement.text("");
                    }, 10000);
                } else {
                    errorMessageElement.text("");
                    rpc.query({
                        model: 'sale.order',
                        method: 'read',
                        args: [[parseInt(selectedSaleOrderId)], ['is_warranty_check']],
                    }).then(function (saleOrderData) {
                        if (saleOrderData && saleOrderData[0] && saleOrderData[0].is_warranty_check === true) {
                            rpc.query({
                                model: 'product.product',
                                method: 'read',
                                args: [[parseInt(selectedProductId)], ['is_warranty_available']],
                            }).then(function (productData) {
                                if (productData && productData[0] && productData[0].is_warranty_available === true) {
                                    rpc.query({
                                        model: 'warranty.claim',
                                        method: 'create',
                                        args: [{
                                            'sale_order_id': parseInt(selectedSaleOrderId),
                                            'customer_id': parseInt(selectedCustomerId),
                                            'product_id': parseInt(selectedProductId),
                                        }],
                                    }).then(function (result) {
                                        window.location.href = '/warranty/claim/submit';
                                    });
                                } else {
                                    errorMessageElement.text("Selected product does not have warranty available.");
                                    setTimeout(function () {
                                        errorMessageElement.text("");
                                    }, 10000);
                                }
                            });
                        } else {
                            errorMessageElement.text("Selected sale order does not have warranty available.");
                            setTimeout(function () {
                                errorMessageElement.text("");
                            }, 10000);
                        }
                    });
                }
            });
        }
    }
});
return publicWidget.registry.WarrantyClaim;
