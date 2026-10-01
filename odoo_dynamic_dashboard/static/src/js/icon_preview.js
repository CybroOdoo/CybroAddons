/** @odoo-module **/

/**
 * Cybrosys Technologies Pvt. Ltd.
 *
 * Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
 * Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
 *
 * This program is under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
 * (AGPL v3), Version 3.
 */

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

import { Component, useState, useEffect, onWillUpdateProps } from "@odoo/owl";

export class IconPreviewJsonField extends Component {
    static template = "odoo_dynamic_dashboard.IconPreviewWidget";
    static props = {
        ...standardFieldProps,
    };
    setup() {
        this.state = useState({
            icon_config: this.props.record.data.icon_style_json
        });
        onWillUpdateProps((nextProps) => { });
        useEffect(
            (value) => {
            }
        );
    }

}

export const iconPreviewJsonField = {
    component: IconPreviewJsonField,
    supportedTypes: ["json"],
};

registry.category("fields").add("icon_preview", iconPreviewJsonField);