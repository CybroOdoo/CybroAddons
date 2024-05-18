/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { TranslationDialog } from "@web/views/fields/translation_dialog";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
patch(TranslationDialog.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService('orm');
        this.notification = useService("notification")
    },
    async translate() {
    /** Function to translate the terms into the selected languages in the settings **/
        const languages = Array.from(new Set(this.terms.map(term => term.lang)));
        const term = this.props.userLanguageValue
            const translations = await this.orm.call("translation.helper",
                 "translate_term", [term,languages]);
                this.terms.forEach(term => {
                const translation = translations[term.lang];
                if (translation) {
                    term.value = translation;
                    this.updatedTerms[term]
            }
            });
            try {
                await this.orm.call(this.props.resModel, "update_field_translations", [
                [this.props.resId],
                this.props.fieldName,
                translations,
                ])
            } catch (error) {
                return this.notification.add(_t("unable to translate"), { type: 'warning'});
            }
             await this.props.onSave();
             this.props.close();
    },
});
