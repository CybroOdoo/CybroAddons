import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

/**
 * "Learn more" link for a premium feature. Unlike a `type="object"` button it
 * opens the feature dialog without saving the record being edited, so it can
 * be used on a new or unsaved form.
 */
export class PharmaPremiumLearnMore extends Component {
    static template = "pharmaceutical_base.PharmaPremiumLearnMore";
    static props = {
        ...standardWidgetProps,
        feature: { type: String },
        label: { type: String, optional: true },
        className: { type: String, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
    }

    get label() {
        return this.props.label || _t("Learn more");
    }

    async onClick() {
        const action = await this.orm.call(
            "pharma.premium.feature",
            "action_open_dialog_by_code",
            [this.props.feature],
        );
        await this.action.doAction(action);
    }
}

export const pharmaPremiumLearnMore = {
    component: PharmaPremiumLearnMore,
    extractProps: ({ attrs }) => ({
        feature: attrs.feature,
        label: attrs.label,
        className: attrs.class_name,
    }),
};

registry.category("view_widgets").add("pharma_premium_learn_more", pharmaPremiumLearnMore);
