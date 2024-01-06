/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { TranslationDialog } from "@web/views/fields/translation_dialog";
import rpc from 'web.rpc';

patch(TranslationDialog.prototype, "translation_dialog_patch", {
    setup() {
        this._super.apply(this, arguments);
    },
    async translate() {
//    Function to translate the terms into the selected languages in the settings
        console.log(this,'this')
        const languages = Array.from(new Set(this.terms.map(term => term.lang)));
        const term = this.props.userLanguageValue
            const translations = await rpc.query({
                model: 'translation.helper',
                method: 'translate_term',
                args: [term, languages],
            });
                this.terms.forEach(term => {
                const translation = translations[term.lang];
                if (translation) {
                    term.value = translation;
                    this.updatedTerms[term]
            }
            });
            await this.orm.call(this.props.resModel, "update_field_translations", [
            [this.props.resId],
            this.props.fieldName,
            translations,
            ])
             this.props.onSave();
             this.props.close();
    },
});
