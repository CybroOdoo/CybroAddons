/** @odoo-module **/
import { registry } from "@web/core/registry";
import { CharField } from "@web/views/fields/char/char_field";
import time from 'web.time';
var translation = require('web.translation');
const rpc = require('web.rpc')
var Dialog = require('web.Dialog');
var _t = translation._t;
const { Component,useRef,onMounted} = owl;
let x;
export class transliterate extends Component {
    static template = 'FieldTextTransliterate'
    setup() {
          super.setup();
    }
     onSelectDateField(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var self = this;
        rpc.query({
            model: 'res.config.settings',
            method: 'get_config_value',
            args: ['transliterate_widget.dest_lang'],
        }).then(function (result) {
            var options = {
                sourceLanguage: google.elements.transliteration.LanguageCode.ENGLISH,
                destinationLanguage: [result],
                shortcutKey: 'ctrl+g',
                transliterationEnabled: true
            };
            var control = new google.elements.transliteration.TransliterationControl(options);
            control.makeTransliteratable($('.input_transliterate'));
        });
    }

}

registry.category("fields").add("transliterate", transliterate);