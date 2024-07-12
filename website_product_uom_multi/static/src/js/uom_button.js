/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { WebsiteSale } from '@website_sale/js/website_sale';
import { OptionalProductsModal } from "@website_sale_product_configurator/js/sale_product_configurator_modal";
import { jsonrpc } from "@web/core/network/rpc_service";
import VariantMixin from "@website_sale/js/sale_variant_mixin";

publicWidget.registry.UomDropDown = publicWidget.Widget.extend(VariantMixin,{
        selector: '.o_uom_dropdown',
    events: {
          'change #o_uom_dropdown': '_onChangeSelect',

    },
         init(ev) {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
        this.orm = this.bindService("orm");
    },


        _onChangeSelect: function(ev){
        var self = this
        var $parent = $(ev.target).closest('.js_product');
        var $default_price = $parent.find(".oe_default_price:first .oe_currency_value");
        var quantity = $parent.find('.css_quantity');
        var price = $default_price.text().trim();
        var uom_id = ev.target.value
        var productID = ev.target.getAttribute('data')
        this._getCombinationInfo(ev)
        },

        _getCombinationInfo: function (ev) {
        if ($(ev.target).hasClass('variant_custom_value')) {
            return Promise.resolve();
        }

        const $parent = $(ev.target).closest('.js_product');
        if(!$parent.length){
            return Promise.resolve();
        }
        const combination = this.getSelectedVariantValues($parent);
        let parentCombination;

        if ($parent.hasClass('main_product')) {
            parentCombination = $parent.find('ul[data-attribute_exclusions]').data('attribute_exclusions').parent_combination;
            const $optProducts = $parent.parent().find(`[data-parent-unique-id='${$parent.data('uniqueId')}']`);

            for (const optionalProduct of $optProducts) {
                const $currentOptionalProduct = $(optionalProduct);
                const childCombination = this.getSelectedVariantValues($currentOptionalProduct);
                const productTemplateId = parseInt($currentOptionalProduct.find('.product_template_id').val());
                jsonrpc('/website_sale/get_combination_info', {
                    'product_template_id': productTemplateId,
                    'product_id': this._getProductId($currentOptionalProduct),
                    'combination': childCombination,
                    'add_qty': parseInt($currentOptionalProduct.find('input[name="add_qty"]').val()),
                    'uom': parseInt($parent.find('select#o_uom_dropdown.form-control').val()),
                    'parent_combination': combination,
                    'context': this.context,
                    ...this._getOptionalCombinationInfoParam($currentOptionalProduct),
                }).then((combinationData) => {
                    if (this._shouldIgnoreRpcResult()) {
                        return;
                    }
                    this._onChangeCombination(ev, $currentOptionalProduct, combinationData);
                    this._checkExclusions($currentOptionalProduct, childCombination, combinationData.parent_exclusions);
                });
            }
        } else {
            parentCombination = this.getSelectedVariantValues(
                $parent.parent().find('.js_product.in_cart.main_product')
            );
        }

        return jsonrpc('/website_sale/get_combination_info', {
            'product_template_id': parseInt($parent.find('.product_template_id').val()),
            'product_id': this._getProductId($parent),
            'combination': combination,
            'add_qty': parseInt($parent.find('input[name="add_qty"]').val()),
            'parent_combination': parentCombination,
            'uom': parseInt($parent.find('select#o_uom_dropdown.form-control').val()),
            'context': this.context,
            ...this._getOptionalCombinationInfoParam($parent),
        }).then((combinationData) => {
            if (this._shouldIgnoreRpcResult()) {
                return;
            }
            this._onChangeCombination(ev, $parent, combinationData);
            this._checkExclusions($parent, combination, combinationData.parent_exclusions);
        });
    },
});



publicWidget.registry.WebsiteSale.include({
    _updateRootProduct($form, productId) {
        this.rootProduct = {
            product_id: productId,
            quantity: parseFloat($form.find('input[name="add_qty"]').val() || 1),
            product_custom_attribute_values: this.getCustomVariantValues($form.find('.js_product')),
            variant_values: this.getSelectedVariantValues($form.find('.js_product')),
            no_variant_attribute_values: this.getNoVariantAttributeValues($form.find('.js_product')),
            uom_id: parseInt($form.find('select#o_uom_dropdown.form-control').val()) // Include the uom_id in the rootProduct object
        };
    },

    _getCombinationInfo: function (ev) {
        if ($(ev.target).hasClass('variant_custom_value')) {
            return Promise.resolve();
        }

        const $parent = $(ev.target).closest('.js_product');
        if(!$parent.length){
            return Promise.resolve();
        }
        const combination = this.getSelectedVariantValues($parent);
        let parentCombination;

        if ($parent.hasClass('main_product')) {
            parentCombination = $parent.find('ul[data-attribute_exclusions]').data('attribute_exclusions').parent_combination;

            const $optProducts = $parent.parent().find(`[data-parent-unique-id='${$parent.data('uniqueId')}']`);

            for (const optionalProduct of $optProducts) {
                const $currentOptionalProduct = $(optionalProduct);
                const childCombination = this.getSelectedVariantValues($currentOptionalProduct);
                const productTemplateId = parseInt($currentOptionalProduct.find('.product_template_id').val());
                jsonrpc('/website_sale/get_combination_info', {
                    'product_template_id': productTemplateId,
                    'product_id': this._getProductId($currentOptionalProduct),
                    'combination': childCombination,
                    'add_qty': parseInt($currentOptionalProduct.find('input[name="add_qty"]').val()),
                    'uom': parseInt($parent.find('select#o_uom_dropdown.form-control').val()),
                    'parent_combination': combination,
                    'context': this.context,
                    ...this._getOptionalCombinationInfoParam($currentOptionalProduct),
                }).then((combinationData) => {
                    if (this._shouldIgnoreRpcResult()) {
                        return;
                    }
                    this._onChangeCombination(ev, $currentOptionalProduct, combinationData);
                    this._checkExclusions($currentOptionalProduct, childCombination, combinationData.parent_exclusions);
                });
            }
        } else {
            parentCombination = this.getSelectedVariantValues(
                $parent.parent().find('.js_product.in_cart.main_product')
            );
        }

        return jsonrpc('/website_sale/get_combination_info', {
            'product_template_id': parseInt($parent.find('.product_template_id').val()),
            'product_id': this._getProductId($parent),
            'combination': combination,
            'add_qty': parseInt($parent.find('input[name="add_qty"]').val()),
            'parent_combination': parentCombination,
            'uom': parseInt($parent.find('select#o_uom_dropdown.form-control').val()),
            'context': this.context,
            ...this._getOptionalCombinationInfoParam($parent),
        }).then((combinationData) => {
            if (this._shouldIgnoreRpcResult()) {
                return;
            }
            this._onChangeCombination(ev, $parent, combinationData);
            this._checkExclusions($parent, combination, combinationData.parent_exclusions);
        });
    },


});

OptionalProductsModal.include({

    getAndCreateSelectedProducts: async function () {
    const self = this;
        const products = [];
        for (const product of self.$modal.find('.js_product.in_cart')) {
            const $item = $(product);
            const quantity = parseFloat($item.find('input[name="add_qty"]').val().replace(',', '.') || 1);
            const parentUniqueId = product.dataset.parentUniqueId;
            const uniqueId = product.dataset.uniqueId;
            const uomId = self.rootProduct.uom_id
            const productCustomVariantValues = $item.find('.custom-attribute-info').data("attribute-value") || self.getCustomVariantValues($item);
            const noVariantAttributeValues = $item.find('.no-attribute-info').data("attribute-value") || self.getNoVariantAttributeValues($item);

            const productID = await self.selectOrCreateProduct(
                $item,
                parseInt($item.find('input.product_id').val(), 10),
                parseInt($item.find('input.product_template_id').val(), 10),
                true
            );

            products.push({
                'product_id': productID,
                'product_template_id': parseInt($item.find('input.product_template_id').val(), 10),
                'quantity': quantity,
                'parent_unique_id': parentUniqueId,
                'unique_id': uniqueId,
                'uom_id': uomId,
                'product_custom_attribute_values': productCustomVariantValues,
                'no_variant_attribute_values': noVariantAttributeValues
            });
        }
        return products;
    },
        _onChangeCombination: function (ev, $parent, combination) {
        $parent
            .find('.td-product_name .product-name')
            .first()
            .text(combination.display_name);
        this._computePriceTotal();
    }
});
