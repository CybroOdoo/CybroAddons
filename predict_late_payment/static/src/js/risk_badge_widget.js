/** @odoo-module **/
/**
 * Risk Badge Widget
 * Displays a coloured pill badge for the payment risk level.
 */
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component } from "@odoo/owl";

const RISK_CONFIG = {
    low:      { label: "Low Risk",      color: "#28a745" },
    medium:   { label: "Medium Risk",   color: "#ffc107" },
    high:     { label: "High Risk",     color: "#fd7e14" },
    critical: { label: "Critical Risk", color: "#dc3545" },
};

class RiskBadgeField extends Component {
    static template = "predict_late_payment.RiskBadgeField";
    static props = { ...standardFieldProps };

    get config() {
        return RISK_CONFIG[this.props.record.data[this.props.name]] || {
            label: "Unknown", color: "#6c757d"
        };
    }
}

// Inline template
RiskBadgeField.template = {
    type: "xml",
    content: /* xml */`
        <span t-attf-style="background: #{config.color}; color: #fff;
                             padding: 3px 10px; border-radius: 12px;
                             font-size: 0.8rem; font-weight: 600;">
            <t t-esc="config.label"/>
        </span>
    `,
};

registry.category("fields").add("risk_badge", {
    component: RiskBadgeField,
});