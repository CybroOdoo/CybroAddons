/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.WarrantyClaim = publicWidget.Widget.extend({
    selector: '.container',
    events: {
        'change #customer_id': '_onChangeCustomer',
        'change #sale_order_id': '_onChangeSaleOrder',
        'submit #form_submit': '_onSubmit'
    },

    _onChangeCustomer: function (ev) {
        //    To show the sale order of the selected customer only
        ev.preventDefault();
        var selectedCustomerId = this.$('#customer_id').val();
        var $saleOrderDropdown = this.$('#sale_order_id');
        var $productDropdown = this.$('#products_id');
        $saleOrderDropdown.empty().append('<option value="">Select Sale Order</option>').prop('disabled', true);
        $productDropdown.empty().append('<option value="">Select Product</option>').prop('disabled', true);
        if (selectedCustomerId) {
            rpc('/partner/sale_order', {
                'partner_id': parseInt(selectedCustomerId)
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

    _onChangeSaleOrder: function (ev) {
        //    get the product details of the selected sale order
        ev.preventDefault();
        var selectedSaleOrderId = this.$('#sale_order_id').val();
        var $productDropdown = this.$('#products_id');
        $productDropdown.empty().append('<option value="">Select Product</option>').prop('disabled', true);
        var self = this
        if (selectedSaleOrderId) {
            rpc('/partner/sale_order_line', {
                'order_id': parseInt(selectedSaleOrderId)
            }).then(function (result) {
                var $productDropdown = self.$('#products_id');
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
        var self = this
        ev.preventDefault();
        // Get the selected sale order ID, customer ID, and product ID
        var selectedSaleOrderId = this.$('#sale_order_id').val();
        var selectedCustomerId = this.$('#customer_id').val();
        var selectedProductId = this.$('#products_id').val();
        var errorMessageElement = this.$('#error_message');
        if (selectedSaleOrderId && selectedCustomerId && selectedProductId) {
            rpc('/partner/warranty_claim_count', {
                'sale_order_id': parseInt(selectedSaleOrderId)
            }).then(function (count) {
                if (count > 0) {
                    errorMessageElement.text("A warranty claim for this sale order already exists.");
                    setTimeout(function () {
                        errorMessageElement.text("");
                    }, 10000);
                } else {
                    errorMessageElement.text("");
                    rpc('/read/sale_order', {
                        'order_id': parseInt(selectedSaleOrderId),
                    }).then(function (saleOrderData) {
                        if (saleOrderData && saleOrderData[0] && saleOrderData[0].is_warranty_check === true) {
                            rpc('/check/selected_product', {
                                'product_id': parseInt(selectedProductId)
                            }).then(function (productData) {
                                if (productData && productData[0] && productData[0].is_warranty_available === true) {
                                    rpc('/create_warranty_claim', {
                                        'sale_order_id': parseInt(selectedSaleOrderId),
                                        'customer_id': parseInt(selectedCustomerId),
                                        'product_id': parseInt(selectedProductId),
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
