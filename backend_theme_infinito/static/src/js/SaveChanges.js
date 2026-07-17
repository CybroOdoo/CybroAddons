/** @odoo-module **/
import {Component} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";
import {useService} from "@web/core/utils/hooks";
import {_t} from "@web/core/l10n/translation";
import {rpc} from "@web/core/network/rpc";
import {browser} from "@web/core/browser/browser";

export class SaveChanges extends Component {
    setup() {
        this.actionService = useService("action");
    }

    async _onClickApply() {
        var self = this;
        var styles = this.props.tools;
        var changed_styles = [];
        for (var i = 0; i < styles.length; i++) {
            changed_styles.push(styles[i]);
        }
        var changed_style_json = {};
        for (var i in changed_styles) {
            changed_style_json[changed_styles[i]] = styles[changed_styles[i]];
        }
        await rpc('/theme_studio/save_styles', {
            method: 'call',
            kwargs: {
                'changed_styles': JSON.stringify(changed_style_json),
                'object_class': self.props.targetClass,
            }
        })
        browser.location.search = "?debug=assets";
        this.env.dialogData.close();
    }

    handleCloseDialog() {
        this.env.dialogData.close();
    }
}

SaveChanges.template = "backend_theme_infinito.saveChanges";
SaveChanges.components = {Dialog};
SaveChanges.props = {
    confirmLabel: {type: String, optional: true},
    confirmClass: {type: String, optional: true},
    cancelLabel: {type: String, optional: true},
    tools: Object,
    targetClass: {type: String, optional: true},
    close: {type: Function, optional: true},
};
SaveChanges.defaultProps = {
    confirmLabel: _t("Save"),
    confirmClass: "btn-primary",
    cancelLabel: _t("Discard")
};
