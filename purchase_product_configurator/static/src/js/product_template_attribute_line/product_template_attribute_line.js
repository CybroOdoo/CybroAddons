import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { formatCurrency } from "@web/core/currency";
import { getSelectedCustomPtav } from "../purchase_utils";

export class ProductTemplateAttributeLine extends Component {
    static template = "purchase_product_configurator.ProductTemplateAttributeLine";
    static props = {
        productTmplId: Number,
        id: Number,
        attribute: {
            type: Object,
            shape: {
                id: Number,
                name: String,
                display_type: {
                    type: String,
                    validate: type => [
                        "color",
                        "multi",
                        "pills",
                        "radio",
                        "select",
                        "image",
                    ].includes(type),
                },
            },
        },
        attribute_values: {
            type: Array,
            element: {
                type: Object,
                shape: {
                    id: Number,
                    name: String,
                    html_color: [Boolean, String],
                    image: [Boolean, String],
                    is_custom: Boolean,
                    price_extra: { type: Number, optional: true },
                    excluded: { type: Boolean, optional: true },
                },
            },
        },
        selected_attribute_value_ids: { type: Array, element: Number },
        create_variant: {
            type: String,
            validate: type => ["always", "dynamic", "no_variant"].includes(type),
        },
        customValue: { type: [{ value: false }, String], optional: true },
    };

    updateSelectedPTAV(ev) {
        this.env.updateProductTemplateSelectedPTAV(
            this.props.productTmplId,
            this.props.id,
            ev.target.value,
            this.props.attribute.display_type === 'multi'
        );
    }

    updateCustomValue(ev) {
        this.env.updatePTAVCustomValue(
            this.props.productTmplId,
            this.props.selected_attribute_value_ids[0],
            ev.target.value
        );
    }

    getPTAVTemplate() {
        switch (this.props.attribute.display_type) {
            case 'select':
                return 'purchase_product_configurator.ptav_select';
            case 'radio':
                return 'purchase_product_configurator.ptav_radio';
            case 'pills':
                return 'purchase_product_configurator.ptav_pills';
            case 'color':
                return 'purchase_product_configurator.ptav_color';
            case 'multi':
                return 'purchase_product_configurator.ptav_multi';
            case 'image':
                return 'purchase_product_configurator.ptav_image';
            default:
                return 'purchase_product_configurator.ptav_select';
        }
    }

    getPTAVSelectName(ptav) {
        if (ptav.price_extra) {
            const sign = ptav.price_extra > 0 ? '+' : '-';
            const currencyId = this.env.currencyId || this.env.currency?.id;
            const price = formatCurrency(Math.abs(ptav.price_extra), currencyId);
            return `${ptav.name} (${sign} ${price})`;
        }
        return ptav.name;
    }

    isSelectedPTAVCustom() {
        return !!getSelectedCustomPtav(this.props);
    }

    get showValuesChoice() {
        return (
            (this.env.canChangeVariant || this.props.create_variant === 'no_variant')
            && (
                this.props.attribute_values.length > 1
                || this.props.attribute.display_type === 'multi'
            )
        );
    }

    get customValuePlaceholder() {
        return _t("Enter a customized value");
    }

    hasPTAVCustom() {
        return this.props.attribute_values.some(ptav => ptav.is_custom);
    }
}
