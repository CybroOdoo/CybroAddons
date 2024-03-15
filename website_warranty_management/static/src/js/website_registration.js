/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.WarrantyClaim = publicWidget.Widget.extend({
    selector: '.container',
    events: {
        'click #customer_id': '_onClickCustomer',
        'click #sale_order_id': '_onClickSaleOrder',
        'submit #form_submit': '_onSubmit'
    },
    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
    },
    async _onClickCustomer(ev) {
        ev.preventDefault();
        var selectedCustomerId = this.$('#customer_id').val();
        if (selectedCustomerId) {
            var NameId = parseInt(selectedCustomerId);
            await this.orm.call("sale.order", "search_read", [[['partner_id', '=', parseInt(selectedCustomerId)]]]).then(function (result) {
                var $saleOrderDropdown = $('#sale_order_id');
                $saleOrderDropdown.empty();
                $.each(result, function (i, saleOrder) {
                    $saleOrderDropdown.append($('<option>', {
                        value: saleOrder.id,
                        text: saleOrder.name,
                    }));
                });
            });
        }
    },
    async _onClickSaleOrder(ev) {
        ev.preventDefault();
        var selectedSaleOrderId = $('#sale_order_id').val();
        if (selectedSaleOrderId) {
            await this.orm.call("sale.order.line", "search_read", [[['order_id', '=', parseInt(selectedSaleOrderId)]]]).then(function (result) {
                var $productDropdown = $('#products_id');
                $productDropdown.empty();
                $.each(result, function (i, saleOrderLine) {
                    $.each(result, function (i, saleOrderLine) {
                        $productDropdown.append($('<option>', {
                            value: saleOrderLine.product_id[0],  // Assuming product_id is a many2one field
                            text: saleOrderLine.product_id[1],  // Assuming product_id has a name field
                        }));
                    });
                });
            });
        }
    },
    async _onSubmit(ev) {
        ev.preventDefault();
        // Get the selected sale order ID, customer ID, and product ID
        var self = this;
        var selectedSaleOrderId = $('#sale_order_id').val();
        var selectedCustomerId = $('#customer_id').val();
        var selectedProductId = $('#products_id').val();
        var errorMessageElement = $('#error_message');
        if (selectedSaleOrderId && selectedCustomerId && selectedProductId) {
            await self.orm.call('warranty.claim', "search_count", [[['sale_order_id', '=', parseInt(selectedSaleOrderId)]]]).then(function (count) {
                if (count > 0) {
                    errorMessageElement.text("A warranty claim for this sale order already exists.");
                    setTimeout(function () {
                        errorMessageElement.text("");
                    }, 10000);
                } else {
                    errorMessageElement.text("");
                    self.orm.call('sale.order', 'read', [[parseInt(selectedSaleOrderId)], ['is_warranty_check']]).then(function (saleOrderData) {
                        if (saleOrderData && saleOrderData[0] && saleOrderData[0].is_warranty_check === true) {
                            self.orm.call('product.product', 'read', [[parseInt(selectedProductId)], ['is_warranty_available']], ).then(function (productData) {
                                if (productData && productData[0] && productData[0].is_warranty_available === true) {
                                    self.orm.call('warranty.claim', 'create', [{
                                        'sale_order_id': parseInt(selectedSaleOrderId),
                                        'customer_id': parseInt(selectedCustomerId),
                                        'product_id': parseInt(selectedProductId),
                                    }], ).then(function (result) {
                                        window.location.href = '/warranty/claim/submit';
                                    });
                                }
                            });
                        } else {
                            errorMessageElement.text("Selected product does not have warranty available.");
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
