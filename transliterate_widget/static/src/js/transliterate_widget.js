/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
const { Component,useRef} = owl;

export class Transliterate extends Component {
//    Setup method to run after the component construction
    setup() {
          super.setup();
            this.orm = useService("orm");
            this.transliterate_text = useRef("transliterate");
    }
//    onSelectTextField method to work when click happens in input field
     async onSelectTextField(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var result = await this.orm.call("ir.config_parameter", "get_param", ['transliterate_widget.destination_language']);
            var options = {
                sourceLanguage: google.elements.transliteration.LanguageCode.ENGLISH,
                destinationLanguage: [result],
                shortcutKey: 'ctrl+g',
                transliterationEnabled: true
            };
            var control = new google.elements.transliteration.TransliterationControl(options);
            control.makeTransliteratable([this.transliterate_text.el]);
    }
}
export const transliterate = {
    component: Transliterate,
};
Transliterate.template = "transliterate_widget.FieldTextTransliterate";
registry.category("fields").add("transliterate", transliterate);
