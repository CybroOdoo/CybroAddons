import { PurchaseOrderLineProductField } from '@purchase_product_matrix/js/purchase_product_field';
import { x2ManyCommands } from "@web/core/orm_plugin";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { PurchaseProductConfiguratorDialog } from "./product_configurator_dialog/product_configurator_dialog";
import { getSelectedCustomPtav } from "./purchase_utils";

async function applyProduct(record, product) {
    // Handle custom values and no-variants
    const customAttributesCommands = [
        x2ManyCommands.set([]),
    ];
    for (const ptal of product.attribute_lines) {
        const selectedCustomPTAV = getSelectedCustomPtav(ptal);
        if (selectedCustomPTAV) {
            customAttributesCommands.push(
                x2ManyCommands.create(undefined, {
                    custom_product_template_attribute_value_id: [
                        selectedCustomPTAV.id,
                        selectedCustomPTAV.name || "",
                    ],
                    custom_value: ptal.customValue,
                })
            );
        }
    }

    const noVariantPTAVIds = product.attribute_lines
        .filter((ptal) => ptal.create_variant === "no_variant")
        .flatMap((ptal) => ptal.selected_attribute_value_ids);

    const update_values = {
        product_id: { id: product.id, display_name: product.display_name },
        product_qty: product.quantity,
        product_no_variant_attribute_value_ids: [x2ManyCommands.set(noVariantPTAVIds)],
    };
    if (product.uom) {
        update_values.product_uom_id = product.uom;
    }
    await record._update(update_values);
    await record.update({ product_qty: product.quantity });
    await record.update({
        purchase_product_custom_attribute_value_ids: customAttributesCommands,
    });
}

patch(PurchaseOrderLineProductField.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialog = useService("dialog");
        this.orm = useService("orm");
    },
    async _onProductTemplateUpdate() {
        const result = await this.orm.call(
            'product.template',
            'get_single_product_variant',
            [this.props.record.data.product_template_id.id],
            {
                context: this.context,
            }
        );
        if (result && result.product_id) {
            if (this.props.record.data.product_id !== result.product_id.id) {
                if (result.has_optional_products) {
                    this._openProductConfigurator();
                } else {
                    await this.props.record.update({
                        product_id: {
                            id: result.product_id,
                            display_name: result.product_name,
                        },
                    });
                }
            }
        } else if (!result.mode || result.mode === 'configurator') {
            this._openProductConfigurator();
        } else {
            this._openGridConfigurator();
        }
    },
    async onEditConfiguration() {
        if (this.props.record.data.is_configurable_product) {
            const product_config_mode = await this.orm.read(
                'product.template',
                [this.props.record.data.product_template_id.id],
                ["product_config_mode"]
            );
            if (
                !product_config_mode[0].product_config_mode
                || product_config_mode[0].product_config_mode === 'configurator'
            ) {
                this._openProductConfigurator(true);
            } else {
                this.matrixConfigurator.open(this.props.record, true);
            }
        }
    },

    async _openGridConfigurator(edit = false) {
        return this.matrixConfigurator.open(this.props.record, edit);
    },

    /**
     * Checks if the template is configurable.
     */
    get isConfigurableTemplate() {
        return super.isConfigurableTemplate || this.props.record.data.is_configurable_product;
    },

    /**
     * Opens the product configurator.
     */
    async _openProductConfigurator(edit = false) {
        const purchaseOrderRecord = this.props.record.model.root;
        const purchaseOrderLine = this.props.record.data;
        let ptavIds = (
            this.props.record.data.product_template_attribute_value_ids?.records?.map(
                record => record.resId
            ) || []
        );

        let customPtavs = [];
        if (edit) {
            ptavIds = this._getNoVariantPtavIds(purchaseOrderLine);
            const noVariantRecords = (
                this.props.record.data.product_no_variant_attribute_value_ids?.records || []
            );
            ptavIds = ptavIds.concat(noVariantRecords.map(record => record.resId));
            customPtavs = await this._getCustomPtavs(purchaseOrderLine);
        }
        const templateId = (
            this.props.record.data.product_template_id?.id
            || this.props.record.data.product_template_id
        );
        const companyId = (
            purchaseOrderRecord.data.company_id?.id
            || purchaseOrderRecord.data.company_id
        );
        const currencyId = (
            this.props.record.data.currency_id?.id
            || this.props.record.data.currency_id
        );

        this.dialog.add(PurchaseProductConfiguratorDialog, {
            productTemplateId: templateId,
            ptavIds: ptavIds,
            customAttributeValues: customPtavs,
            quantity: this.props.record.data.product_qty > 0 ? this.props.record.data.product_qty : 1,
            companyId: companyId,
            currencyId: currencyId,
            edit: edit,
            save: async (mainProduct, optionalProducts) => {
                await Promise.all([
                    applyProduct(this.props.record, mainProduct),
                    ...optionalProducts.map(async product => {
                        const line = await purchaseOrderRecord.data.order_line.addNewRecord({
                            position: 'bottom',
                            mode: 'readonly',
                        });
                        await applyProduct(line, product);
                    }),
                ]);
                purchaseOrderRecord.data.order_line.leaveEditMode();
            },
            discard: () => {
                purchaseOrderRecord.data.order_line.delete(this.props.record);
            },
        });
    },

    _getNoVariantPtavIds(purchaseOrderLine) {
        return purchaseOrderLine.product_template_attribute_value_ids?.currentIds || [];
    },

    /**
     * Return the custom PTAVs of the provided purchase order line.
     *
     * @param purchaseOrderLine The purchase order line
     * @return {Promise<CustomPtav[]>} The purchase order line's custom PTAVs.
     */
    async _getCustomPtavs(purchaseOrderLine) {
        const customPtavIds = purchaseOrderLine.purchase_product_custom_attribute_value_ids;
        if (!customPtavIds) {
            return [];
        }
        let customPtavs = [];
        if (customPtavIds.records?.[0]?.isNew) {
            customPtavs = customPtavIds.records.map(record => record.data);
        } else if (customPtavIds.currentIds?.length) {
            const specification = {
                custom_product_template_attribute_value_id: {
                    fields: { id: {} },
                },
                custom_value: {},
            };
            customPtavs = await this.orm.webRead(
                'product.attribute.custom.value',
                customPtavIds.currentIds,
                { specification },
            );
        }
        return customPtavs.map(customPtav => ({
            ptavId: (
                customPtav.custom_product_template_attribute_value_id
                && customPtav.custom_product_template_attribute_value_id.id
            ),
            id: (
                customPtav.custom_product_template_attribute_value_id
                && customPtav.custom_product_template_attribute_value_id.id
            ),
            value: customPtav.custom_value,
        }));
    },
});
