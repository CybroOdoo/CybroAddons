/** @odoo-module **/
/**
     * This file is used to add some features to DomainSelectorDialog .
*/
import { DomainSelectorDialog } from "@web/core/domain_selector_dialog/domain_selector_dialog";
import {useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { Domain } from "@web/core/domain";

patch(DomainSelectorDialog.prototype, 'advanced_search_widget', {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            domain: this.props.domain
        });
        return this._super(...arguments);
    },
    get dialogTitle() {
        //  Return title of the DomainSelectorDialog
        return this.props.title || _t("Domain");
    },
    get domainSelectorProps() {
        // Default domain selector props values
        return {
            className: this.props.className,
            resModel: this.props.resModel,
            readonly: this.props.readonly,
            isDebugMode: this.props.isDebugMode,
            defaultLeafValue: this.props.defaultLeafValue,
            value: this.state.domain || this.props.domain,
            update: (domain) => {
                this.state.domain = domain;
            },
        };
    },
    async onSave() {
        // It will apply the domain as new filter
        if (!this.state.domain){
            this.notification.add(this.env._t("Domain is invalid. Please correct it"), {
                type: "danger",
            });
        }
        else{
            this.props.onSave(this.state.domain);
            this.props.close();
        }
    },
});
DomainSelectorDialog.props = {
    ...DomainSelectorDialog.props,
     onSave: Function,
    title: { type: String, optional: true },
    context: { type: Object, optional: true },
    domain: { type: String, optional: true },
};
