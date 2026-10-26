/** @odoo-module **/

import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { Component, signal, onWillStart } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

class LanguageSystray extends Component {
    setup() {
        this.action = useService("action");
        this.languages = signal([]);
        this.canAddLanguage = user.isSystem;

        onWillStart(async () => {
            const data = await rpc("/easy_language_selector/options");
            this.languages.value = data || [];
        });
    }

    async onChangeLang(ev) {
        const lang_code = ev.target.value;
        if (lang_code === "0") return;

        if (lang_code === "add_extra_lang") {
            if (!this.canAddLanguage) return;
            this.action.doAction("base.res_lang_act_window");
        } else {
            await rpc("/easy_language_selector/change", { code: lang_code });
            this.action.doAction("reload_context");
        }
    }
}

LanguageSystray.template = "LanguageSystray";

const systrayItem = {
    Component: LanguageSystray,
};

registry.category("systray").add("LanguageSystray", systrayItem, { sequence: 50 });
