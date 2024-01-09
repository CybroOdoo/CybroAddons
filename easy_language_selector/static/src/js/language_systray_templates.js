/** @odoo-module **/

import { registry} from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
const { Component, useRef } = owl

class LanguageSystray extends Component{
// Fetch languages into lang_data and call renderLanguage
    async setup() {
        this.action = useService("action");
        this.LanguageSelector = useRef("language_selector");
        this.rpc = useService("rpc");
        const lang_data = await this.rpc("/easy_language_selector/options");
        this.renderLanguage(lang_data)
    }
//  Add the options in the select field
    renderLanguage(data){
        var datas = data;
        var self = this;
        datas.forEach((ev) => {
            const options = document.createElement("option");
            options.value = ev.code;
            options.text = ev.name;
            options.className = 'language_options';
            self.LanguageSelector.el.append(options)
        });
        const option_add_lang = document.createElement("option");
            option_add_lang.value = 'add_extra_lang';
            option_add_lang.text = 'Add Language';
            option_add_lang.className = 'language_options';
            self.LanguageSelector.el.append(option_add_lang)
    }
//  Function for changing language
    async onChangeLang(){
        var self = this;
        var lang_code = this.LanguageSelector.el.value
        if (lang_code == "add_extra_lang") {
            self.action.doAction({
                type: "ir.actions.act_window",
                name: 'Languages',
                res_model: 'res.lang',
                view_mode: 'list',
                views: [
                    [false, 'list'],
                    [false, 'form']
                ],
                target: 'self'
            });
        }else{
            await this.rpc('/easy_language_selector/change',{code : lang_code}).then(function() {
                    return self.action.doAction("reload_context");
            })
        }
    }
}
LanguageSystray.template = "LanguageSystray";
const systrayItem = { Component: LanguageSystray, };
registry.category("systray").add("LanguageSystray", systrayItem);
