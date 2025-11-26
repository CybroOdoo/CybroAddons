/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.WarrantyClaim = publicWidget.Widget.extend({
    selector: '.warranty-claim-widget',
    events: {
        'change #customer_id': '_onClickCustomer',
        'change #sale_order_id': '_onClickSaleOrder',
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
            await this.orm.call("sale.order", "search_read", [
                [['partner_id', '=', parseInt(selectedCustomerId)], ['is_warranty_check', '=', true]],
                ['id', 'name']
            ]).then(function (result) {
                var $saleOrderDropdown = $('#sale_order_id');
                $saleOrderDropdown.empty();
                $saleOrderDropdown.append($('<option>', {
                    value: '',
                    text: 'Select Sale Order'
                }));
                $.each(result, function (i, saleOrder) {
                    $saleOrderDropdown.append($('<option>', {
                        value: saleOrder.id,
                        text: saleOrder.name,
                    }));
                });
            });
            // Clear products dropdown when customer changes
            $('#products_id').empty().append($('<option>', {
                value: '',
                text: 'Select Product'
            }));
        }
    },

    async _onClickSaleOrder(ev) {
        ev.preventDefault();
        var selectedSaleOrderId = $('#sale_order_id').val();
        var $productDropdown = $('#products_id');

        if (selectedSaleOrderId) {
            await this.orm.call("sale.order.line", "search_read", [
                [['order_id', '=', parseInt(selectedSaleOrderId)]],
                ['product_id']
            ]).then(function (result) {
                $productDropdown.empty();
                $productDropdown.append($('<option>', {
                    value: '',
                    text: 'Select Product'
                }));
                $.each(result, function (i, saleOrderLine) {
                    $productDropdown.append($('<option>', {
                        value: saleOrderLine.product_id[0],
                        text: saleOrderLine.product_id[1],
                    }));
                });
            });
        } else {
            $productDropdown.empty();
            $productDropdown.append($('<option>', {
                value: '',
                text: 'Select Product'
            }));
        }
    },

    async _onSubmit(ev) {
        ev.preventDefault();
        var self = this;

        // Get the selected values
        var selectedSaleOrderId = $('#sale_order_id').val();
        var selectedCustomerId = $('#customer_id').val();
        var selectedProductId = $('#products_id').val();
        var errorMessageElement = $('#error_message');

        // Clear previous error messages
        errorMessageElement.text("");

        // Validate all fields are selected
        if (!selectedCustomerId) {
            errorMessageElement.text("Please select a customer.");
            setTimeout(function () {
                errorMessageElement.text("");
            }, 5000);
            return;
        }

        if (!selectedSaleOrderId) {
            errorMessageElement.text("Please select a sale order.");
            setTimeout(function () {
                errorMessageElement.text("");
            }, 5000);
            return;
        }

        if (!selectedProductId) {
            errorMessageElement.text("Please select a product.");
            setTimeout(function () {
                errorMessageElement.text("");
            }, 5000);
            return;
        }

        try {
            // Check if warranty claim already exists for this sale order
            const count = await self.orm.call('warranty.claim', "search_count", [
                [['sale_order_id', '=', parseInt(selectedSaleOrderId)]]
            ]);

            if (count > 0) {
                errorMessageElement.text("A warranty claim for this sale order already exists.");
                setTimeout(function () {
                    errorMessageElement.text("");
                }, 10000);
                return;
            }

            // Check if sale order has warranty
            const saleOrderData = await self.orm.call('sale.order', 'read', [
                [parseInt(selectedSaleOrderId)],
                ['is_warranty_check']
            ]);

            if (!saleOrderData || !saleOrderData[0] || saleOrderData[0].is_warranty_check !== true) {
                errorMessageElement.text("Selected sale order does not have warranty available.");
                setTimeout(function () {
                    errorMessageElement.text("");
                }, 10000);
                return;
            }

            // Check if product has warranty
            const productData = await self.orm.call('product.product', 'read', [
                [parseInt(selectedProductId)],
                ['is_warranty_available']
            ]);

            if (!productData || !productData[0] || productData[0].is_warranty_available !== true) {
                errorMessageElement.text("Selected product does not have warranty available.");
                setTimeout(function () {
                    errorMessageElement.text("");
                }, 10000);
                return;
            }

            // All validations passed, create the warranty claim
            await self.orm.call('warranty.claim', 'create', [{
                'sale_order_id': parseInt(selectedSaleOrderId),
                'customer_id': parseInt(selectedCustomerId),
                'product_id': parseInt(selectedProductId),
            }]);

            // Redirect to success page
            window.location.href = '/warranty/claim/submit';

        } catch (error) {
            console.error('Error creating warranty claim:', error);
            errorMessageElement.text("An error occurred while creating the warranty claim. Please try again.");
            setTimeout(function () {
                errorMessageElement.text("");
            }, 10000);
        }
    }
});

export default publicWidget.registry.WarrantyClaim;