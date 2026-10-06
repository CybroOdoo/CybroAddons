import { t, useProps } from "@odoo/owl";
import { Component } from "@odoo/owl";
/** @odoo-module **/

import {Dialog} from "@web/core/dialog/dialog";
import {_t} from "@web/core/l10n/translation";
import {rpc} from "@web/core/network/rpc";
import {browser} from "@web/core/browser/browser";


export class SaveChanges extends Component {
    props = useProps({
        confirmLabel: t.string().optional(_t("Save")),
        confirmClass: t.string().optional("btn-primary"),
        cancelLabel: t.string().optional(_t("Discard")),
        tools: t.any(),
        extraRules: t.array(t.any()).optional([]),
        targetClass: t.string().optional(),
        close: t.function().optional(),
    });
    setup() {
    }

    async _onClickApply() {
        const rules = [
            { targetClass: this.props.targetClass, styles: this.props.tools },
            ...this.props.extraRules,
        ];
        for (const { targetClass, styles } of rules) {
            const declarations = Object.fromEntries(
                Array.from(styles, name => [name, styles.getPropertyValue(name)])
            );
            if (!Object.keys(declarations).length) continue;
            await rpc('/theme_studio/save_styles', {
                kwargs: {
                    changed_styles: JSON.stringify(declarations),
                    object_class: targetClass,
                },
            });
        }
        browser.location.search = "?debug=assets";
        this.props.close();
    }

    handleCloseDialog() {
        this.props.close();
    }
}

SaveChanges.template = "backend_theme_infinito.saveChanges";
SaveChanges.components = {Dialog};

