odoo.define('translation_helper.translation', function (require) {
"use strict";
    var rpc = require('web.rpc');
    var TranslationDialog = require('web.TranslationDialog');

TranslationDialog.include({
    _loadTranslations: async function () {
            /** Asynchronously loads translations and updates them with the correct values.**/
            const domain = [...this.domain, ['lang', 'in', this.languages.map(l => l[0])]];
            var result =  await this._rpc({
                model: 'ir.translation',
                method: 'search_read',
                fields: ['lang', 'src', 'value'],
                domain: domain,
            });
            var loadLanguages = await this._loadLanguages();
            var languageCodes = loadLanguages.map(language => language[0]);
            const term = this.userLanguageValue;
            const translations = await rpc.query({
                model: 'translation.helper',
                method: 'translate_term',
                args: [term, languageCodes],
            });
            result.forEach(entry => {
                const langCode = entry.lang;
                if (translations[langCode]) {
                    entry.value = translations[langCode];
                }
            });
            return result
        },
});
});