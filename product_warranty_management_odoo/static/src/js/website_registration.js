/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.WarrantyClaim = publicWidget.Widget.extend({
    selector: '.container',

    events: {
        'change #customer_id': '_onClickCustomer',
        'change #sale_order_id': '_onClickSaleOrder',
        'submit #form_submit': '_onSubmit',
    },

    willStart: function () {
        const def = this._super.apply(this, arguments);
        this.rpc = this.bindService("rpc");
        return def;
    },

    _onClickCustomer: function (ev) {
        ev.preventDefault();
        const selectedCustomerId = this.$('#customer_id').val();
        const $saleOrderDropdown = this.$('#sale_order_id');
        const $productDropdown = this.$('#products_id');

        $saleOrderDropdown.empty().append('<option value="">Select Sale Order</option>').prop('disabled', true);
        $productDropdown.empty().append('<option value="">Select Product</option>').prop('disabled', true);

        if (selectedCustomerId) {
            this.rpc('/partner/sale_order', {
                partner_id: parseInt(selectedCustomerId)
            }).then(result => {
                if (Array.isArray(result) && result.length > 0) {
                    $saleOrderDropdown.prop('disabled', false);
                    result.forEach(saleOrder => {
                        $saleOrderDropdown.append($('<option>', {
                            value: saleOrder.id,
                            text: saleOrder.name,
                        }));
                    });
                }
            });
        }
    },

    _onClickSaleOrder: function (ev) {
        ev.preventDefault();
        const selectedSaleOrderId = this.$('#sale_order_id').val();
        const $productDropdown = this.$('#products_id');
        const self = this;

        $productDropdown.empty().append('<option value="">Select Product</option>').prop('disabled', true);

        if (selectedSaleOrderId) {
            this.rpc('/partner/sale_order_line', {
                order_id: parseInt(selectedSaleOrderId)
            }).then(result => {
                if (Array.isArray(result) && result.length > 0) {
                    $productDropdown.prop('disabled', false);
                    result.forEach(saleOrderLine => {
                        if (saleOrderLine.product_id && saleOrderLine.product_id.length === 2) {
                            $productDropdown.append($('<option>', {
                                value: saleOrderLine.product_id[0],
                                text: saleOrderLine.product_id[1],
                            }));
                        }
                    });
                }
            });
        }
    },

    _onSubmit: function (ev) {
        ev.preventDefault();
        const self = this;

        const selectedSaleOrderId = this.$('#sale_order_id').val();
        const selectedCustomerId = this.$('#customer_id').val();
        const selectedProductId = this.$('#products_id').val();
        const errorMessageElement = this.$('#error_message');

        if (selectedSaleOrderId && selectedCustomerId && selectedProductId) {
            this.rpc('/partner/warranty_claim_count', {
                sale_order_id: parseInt(selectedSaleOrderId)
            }).then(count => {
                if (count > 0) {
                    errorMessageElement.text("A warranty claim for this sale order already exists.");
                    setTimeout(() => errorMessageElement.text(""), 10000);
                } else {
                    errorMessageElement.text("");
                    self.rpc('/read/sale_order', {
                        order_id: parseInt(selectedSaleOrderId),
                    }).then(saleOrderData => {
                        const order = saleOrderData && saleOrderData[0];
                        if (order && order.is_warranty_check === true) {
                            self.rpc('/check/selected_product', {
                                product_id: parseInt(selectedProductId)
                            }).then(productData => {
                                const product = productData && productData[0];
                                if (product && product.is_warranty_available === true) {
                                    self.rpc('/create_warranty_claim', {
                                        sale_order_id: parseInt(selectedSaleOrderId),
                                        customer_id: parseInt(selectedCustomerId),
                                        product_id: parseInt(selectedProductId),
                                    }).then(() => {
                                        window.location.href = '/warranty/claim/submit';
                                    });
                                } else {
                                    errorMessageElement.text("Selected product does not have warranty available.");
                                    setTimeout(() => errorMessageElement.text(""), 10000);
                                }
                            });
                        } else {
                            errorMessageElement.text("Selected sale order does not have warranty available.");
                            setTimeout(() => errorMessageElement.text(""), 10000);
                        }
                    });
                }
            });
        } else {
            errorMessageElement.text("Please select all required fields.");
            setTimeout(() => errorMessageElement.text(""), 10000);
        }
    }
});

return publicWidget.registry.WarrantyClaim;
