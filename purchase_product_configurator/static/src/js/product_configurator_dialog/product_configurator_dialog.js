import { _t } from "@web/core/l10n/translation";
import { formatCurrency } from "@web/core/currency";
import { Component, onWillStart, proxy, useSubEnv } from "@odoo/owl";
import { Dialog } from '@web/core/dialog/dialog';
import { PurchaseProductList } from "../product_list/product_list";
import { rpc } from "@web/core/network/rpc";

export class PurchaseProductConfiguratorDialog extends Component {
    static components = { Dialog, PurchaseProductList };
    static template = 'purchase_product_configurator.dialog';
    static props = {
        productTemplateId: Number,
        ptavIds: { type: Array, element: Number },
        customAttributeValues: {
            type: Array,
            element: Object,
            shape: {
                ptavId: { type: Number, optional: true },
                id: { type: Number, optional: true },
                value: String,
            },
        },
        quantity: Number,
        productUOMId: { type: Number, optional: true },
        companyId: { type: Number, optional: true },
        currencyId: Number,
        edit: { type: Boolean, optional: true, default: false },
        save: Function,
        discard: Function,
        close: Function,
    };

    setup() {
        this.title = _t("Configure your product");
        this.rpc = rpc;
        this.state = proxy({
            products: [],
            optionalProducts: [],
        });

        useSubEnv({
            mainProductTmplId: this.props.productTemplateId,
            canChangeVariant: this.props.options?.canChangeVariant ?? true,
            currencyId: this.props.currencyId,
            currency: { id: this.props.currencyId },
            addProduct: this._addProduct.bind(this),
            removeProduct: this._removeProduct.bind(this),
            setQuantity: this._setQuantity.bind(this),
            updateProductTemplateSelectedPTAV: this._updateProductTemplateSelectedPTAV.bind(this),
            updatePTAVCustomValue: this._updatePTAVCustomValue.bind(this),
            isPossibleCombination: this._isPossibleCombination.bind(this),
        });

        onWillStart(async () => {
            const { products, optional_products } = await this._loadData(this.props.edit);
            this.state.products = products || [];
            this.state.optionalProducts = optional_products || [];
            for (const customValue of this.props.customAttributeValues) {
                this._updatePTAVCustomValue(
                    this.env.mainProductTmplId,
                    customValue.ptavId || customValue.id,
                    customValue.value
                );
            }
            if (this.state.products.length) {
                this._checkExclusions(this.state.products[0]);
            }
        });
    }

    async _loadData(onlyMainProduct) {
        return this.rpc('/purchase_product_configurator/get_values', {
            product_template_id: this.props.productTemplateId,
            currency_id: this.props.currencyId,
            quantity: this.props.quantity,
            product_uom_id: this.props.productUOMId,
            company_id: this.props.companyId,
            ptav_ids: this.props.ptavIds,
            only_main_product: onlyMainProduct,
        });
    }

    async _createProduct(product) {
        return this.rpc('/purchase_product_configurator/create_product', {
            product_template_id: product.product_tmpl_id,
            combination: this._getCombination(product),
        });
    }

    async _updateCombination(product, quantity) {
        return this.rpc('/purchase_product_configurator/update_combination', {
            product_template_id: product.product_tmpl_id,
            combination: this._getCombination(product),
            currency_id: this.props.currencyId,
            quantity: quantity,
            product_uom_id: this.props.productUOMId,
            company_id: this.props.companyId,
        });
    }

    async _getOptionalProducts(product) {
        return this.rpc('/purchase_product_configurator/get_optional_products', {
            product_template_id: product.product_tmpl_id,
            combination: this._getCombination(product),
            parent_combination: this._getParentsCombination(product),
            currency_id: this.props.currencyId,
            company_id: this.props.companyId,
        });
    }

    async _addProduct(productTmplId) {
        const index = this.state.optionalProducts.findIndex(
            p => p.product_tmpl_id === productTmplId
        );
        if (index >= 0) {
            this.state.products.push(...this.state.optionalProducts.splice(index, 1));
            const product = this._findProduct(productTmplId);
            let newOptionalProducts = await this._getOptionalProducts(product);
            for (const newOptionalProductDict of newOptionalProducts) {
                const newProduct = this._findProduct(newOptionalProductDict.product_tmpl_id);
                if (newProduct) {
                    newOptionalProducts = newOptionalProducts.filter(
                        (p) => p.product_tmpl_id !== newOptionalProductDict.product_tmpl_id
                    );
                    newProduct.parent_product_tmpl_ids.push(productTmplId);
                }
            }
            if (newOptionalProducts) {
                this.state.optionalProducts.push(...newOptionalProducts);
            }
        }
    }

    _removeProduct(productTmplId) {
        const index = this.state.products.findIndex(p => p.product_tmpl_id === productTmplId);
        if (index >= 0) {
            this.state.optionalProducts.push(...this.state.products.splice(index, 1));
            for (const childProduct of this._getChildProducts(productTmplId)) {
                childProduct.parent_product_tmpl_ids = childProduct.parent_product_tmpl_ids.filter(
                    id => id !== productTmplId
                );
                if (!childProduct.parent_product_tmpl_ids.length) {
                    this._removeProduct(childProduct.product_tmpl_id);
                    this.state.optionalProducts.splice(
                        this.state.optionalProducts.findIndex(
                            p => p.product_tmpl_id === childProduct.product_tmpl_id
                        ),
                        1
                    );
                }
            }
        }
    }

    async _setQuantity(productTmplId, quantity) {
        if (quantity <= 0) {
            if (productTmplId === this.env.mainProductTmplId) {
                const product = this._findProduct(productTmplId);
                const { price } = await this._updateCombination(product, 1);
                product.quantity = 1;
                product.price = parseFloat(price);
                return;
            }
            this._removeProduct(productTmplId);
        } else {
            const product = this._findProduct(productTmplId);
            const { price } = await this._updateCombination(product, quantity);
            product.quantity = quantity;
            product.price = parseFloat(price);
        }
    }

    async _updateProductTemplateSelectedPTAV(productTmplId, ptalId, ptavId, multiIdsAllowed) {
        const product = this._findProduct(productTmplId);
        let selectedIds = product.attribute_lines.find(
            ptal => ptal.id === ptalId
        ).selected_attribute_value_ids;
        if (multiIdsAllowed) {
            const ptavID = parseInt(ptavId, 10);
            if (!selectedIds.includes(ptavID)) {
                selectedIds.push(ptavID);
            } else {
                selectedIds = selectedIds.filter(ptav => ptav !== ptavID);
            }
        } else {
            selectedIds = [parseInt(ptavId, 10)];
        }
        product.attribute_lines.find(
            ptal => ptal.id === ptalId
        ).selected_attribute_value_ids = selectedIds;
        this._checkExclusions(product);
        if (this._isPossibleCombination(product)) {
            const updatedValues = await this._updateCombination(product, product.quantity);
            Object.assign(product, updatedValues);
            if (!product.id && product.attribute_lines.every(ptal => ptal.create_variant === "always")) {
                const combination = this._getCombination(product);
                product.archived_combinations = product.archived_combinations.concat([combination]);
                this._checkExclusions(product);
            }
        }
    }

    _updatePTAVCustomValue(productTmplId, ptavId, customValue) {
        const product = this._findProduct(productTmplId);
        if (!product) {
            return;
        }
        const targetPtal = product.attribute_lines.find(
            ptal => ptal.selected_attribute_value_ids.includes(ptavId)
        );
        if (targetPtal) {
            targetPtal.customValue = customValue;
        }
    }

    _checkExclusions(product, checked = undefined) {
        const combination = this._getCombination(product);
        const exclusions = product.exclusions;
        const parentExclusions = product.parent_exclusions;
        const archivedCombinations = product.archived_combinations;
        const parentCombination = this._getParentsCombination(product);
        const childProducts = this._getChildProducts(product.product_tmpl_id);
        const ptavList = product.attribute_lines.flat().flatMap(ptal => ptal.attribute_values);
        ptavList.forEach(ptav => {
            ptav.excluded = false;
        });
        if (exclusions) {
            for (const ptavId of combination) {
                for (const excludedPtavId of (exclusions[ptavId] || [])) {
                    const match = ptavList.find(ptav => ptav.id === excludedPtavId);
                    if (match) {
                        match.excluded = true;
                    }
                }
            }
        }
        if (parentCombination) {
            for (const ptavId of parentCombination) {
                for (const excludedPtavId of (parentExclusions?.[ptavId] || [])) {
                    const ptav = ptavList.find(ptav => ptav.id === excludedPtavId);
                    if (ptav) {
                        ptav.excluded = true;
                    }
                }
            }
        }
        if (archivedCombinations) {
            for (const excludedCombination of archivedCombinations) {
                const ptavCommon = excludedCombination.filter((ptav) => combination.includes(ptav));
                if (ptavCommon.length === combination.length) {
                    for (const excludedPtavId of ptavCommon) {
                        const match = ptavList.find(ptav => ptav.id === excludedPtavId);
                        if (match) {
                            match.excluded = true;
                        }
                    }
                } else if (ptavCommon.length === (combination.length - 1)) {
                    const disabledPtavId = excludedCombination.find(
                        (ptav) => !combination.includes(ptav)
                    );
                    const excludedPtav = ptavList.find(ptav => ptav.id === disabledPtavId);
                    if (excludedPtav) {
                        excludedPtav.excluded = true;
                    }
                }
            }
        }
        const checkedProducts = checked || [];
        for (const optionalProductTmpl of childProducts) {
            if (!checkedProducts.includes(optionalProductTmpl)) {
                checkedProducts.push(optionalProductTmpl);
                this._checkExclusions(optionalProductTmpl, checkedProducts);
            }
        }
    }

    _findProduct(productTmplId) {
        return (
            this.state.products.find(p => p.product_tmpl_id === productTmplId)
            || this.state.optionalProducts.find(p => p.product_tmpl_id === productTmplId)
        );
    }

    _getChildProducts(productTmplId) {
        return [
            ...this.state.products.filter(p => p.parent_product_tmpl_ids?.includes(productTmplId)),
            ...this.state.optionalProducts.filter(p => p.parent_product_tmpl_ids?.includes(productTmplId)),
        ];
    }

    _getCombination(product) {
        return product.attribute_lines.flatMap(ptal => ptal.selected_attribute_value_ids);
    }

    _getParentsCombination(product) {
        let parentsCombination = [];
        for (const parentProductTmplId of product.parent_product_tmpl_ids || []) {
            parentsCombination.push(this._getCombination(this._findProduct(parentProductTmplId)));
        }
        return parentsCombination.flat();
    }

    _isPossibleCombination(product) {
        return product.attribute_lines.every(ptal => !ptal.attribute_values.find(
            ptav => ptal.selected_attribute_value_ids.includes(ptav.id)
        )?.excluded);
    }

    isPossibleConfiguration() {
        return [...this.state.products].every(
            p => this._isPossibleCombination(p)
        );
    }

    async onConfirm() {
        if (!this.isPossibleConfiguration()) {
            return;
        }
        for (const product of this.state.products) {
            if (
                !product.id
                && product.attribute_lines.some(ptal => ptal.create_variant === "dynamic")
            ) {
                const productId = await this._createProduct(product);
                product.id = parseInt(productId, 10);
            }
        }
        await this.props.save(
            this.state.products.find(
                p => p.product_tmpl_id === this.env.mainProductTmplId
            ),
            this.state.products.filter(
                p => p.product_tmpl_id !== this.env.mainProductTmplId
            ),
        );
        this.props.close();
    }

    get totalMessage() {
        return _t("Total: %s", this.getFormattedTotal());
    }

    getFormattedTotal() {
        const total = (this.state.products || []).reduce(
            (sum, product) => sum + product.price * product.quantity,
            0
        );
        return formatCurrency(total, this.props.currencyId);
    }

    onDiscard() {
        if (!this.props.edit) {
            this.props.discard();
        }
        this.props.close();
    }
}
