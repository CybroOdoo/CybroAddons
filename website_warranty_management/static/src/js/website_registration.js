/**@odoo-module*/
var publicWidget = require('web.public.widget');
var rpc = require('web.rpc');
publicWidget.registry.WarrantyClaim = publicWidget.Widget.extend({
    selector: '.container',
    events: {
        'click #customer_id': '_onClickCustomer',
        'click #sale_order_id': '_onClickSaleOrder',
        'submit #form_submit': '_onSubmit'
    },
    _onClickCustomer:async function (ev) {
    //    To show the sale order of the selected customer only
        ev.preventDefault();
        var selectedCustomerId = this.$('#customer_id').val();
        if (selectedCustomerId) {
            await rpc.query({
                model: 'sale.order',
                method: 'search_read',
                args: [
                    [['partner_id', '=', parseInt(selectedCustomerId)],['is_warranty_check','=',true]],  // Apply domain condition
                    ['name'],  // Fields to read, adjust as needed
                ],
            }).then(function (result) {
                var $saleOrderDropdown = $('#sale_order_id');
                $saleOrderDropdown.empty();
                $.each(result, function (i, saleOrder) {
                    $saleOrderDropdown.append($('<option>', {
                        value: saleOrder.id,
                        text: saleOrder.name,
                    }));
                });
            });
            this._onClickSaleOrder(ev)
        }
    },
     _onClickSaleOrder:async function (ev) {
        ev.preventDefault();
        var selectedSaleOrderId = $('#sale_order_id').val();
        var $productDropdown = $('#products_id');
        if (selectedSaleOrderId) {
            await rpc.query({
                model: 'sale.order.line',
                method: 'search_read',
                args: [
                    [['order_id', '=', parseInt(selectedSaleOrderId)]],  // Apply domain condition
                    ['product_id'],  // Fields to read, adjust as needed
                ],
            }).then(function (result) {
                $productDropdown.empty();
                $.each(result, function (i, saleOrderLine) {
                    $productDropdown.append($('<option>', {
                        value: saleOrderLine.product_id[0],  // Assuming product_id is a many2one field
                        text: saleOrderLine.product_id[1],  // Assuming product_id has a name field
                    }));
                });
            });
        }else{
            $productDropdown.empty()
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
