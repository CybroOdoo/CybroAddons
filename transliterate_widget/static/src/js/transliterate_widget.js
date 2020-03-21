odoo.define('transliterate_widget.TransliterateWidget', function(require) {
    "use strict";
    var field_registry = require('web.field_registry');
    var fields = require('web.basic_fields');
    var rpc = require('web.rpc');

    google.load("elements", "1", {
        packages: "transliteration"
    });

    var FieldTextTransliterate = fields.FieldChar.extend({
        template: 'FieldTextTransliterate',
        widget_class: 'oe_form_field_transliterate',

        events: _.extend({}, fields.FieldChar.prototype.events, {
            'click': '_onSelectField',
        }),

        _onSelectField: function(ev) {
             rpc.query({
                    model: 'res.config.settings',
                    method: 'get_config_value',
                    args: ['transliterate_widget.dest_lang'],
                }, {
                    shadow: true,
                })
                .then(function (result) {
                    var options = {
                        sourceLanguage: google.elements.transliteration.LanguageCode.ENGLISH,
                        destinationLanguage: [result],
                        shortcutKey: 'ctrl+g',
                        transliterationEnabled: true
                    };
                    var control = new google.elements.transliteration.TransliterationControl(options);
                    control.makeTransliteratable($('.input_transliterate'));
                });
        },

    });

    field_registry.add('transliterate', FieldTextTransliterate);
    return {
        FieldTextTransliterate: FieldTextTransliterate
    };


});


