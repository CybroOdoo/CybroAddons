import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { SelectionPopup } from "@point_of_sale/app/components/popups/selection_popup/selection_popup";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
/**
 * OrderlineLanguageSwitchButton is a component responsible for switching the user's preferred language.
 */
patch(ControlButtons.prototype, {
    /**
     * Click event handler for the language switch button.
     */
    async onClick() {
        const resIds = await this.env.services.orm.search("res.lang", [["active", "=", true]])
        if (resIds.length > 0) {
            const fields = ['id','name', 'code'];  // specify the fields you want to fetch
            const availLang = await this.env.services.orm.read("res.lang", resIds, fields);
            const availableLang = availLang
            .filter(lang => lang.code !== user.lang)
            .map(lang => ({
                id: lang.id,
                label: lang.name,
                item: lang.code,
            }));
            const payload = await makeAwaitable(this.dialog, SelectionPopup, {
                title: _t('Available Languages'),
                list: availableLang,
            });
            if (payload) {
                await this.handleLanguageSwitch(payload);
            }
        }
    },
    /**
     * Handles the language switch process.
     *
     * @param {string} selectedLang - The selected language code.
//     */
    async handleLanguageSwitch(selectedLang) {
        try {
            await rpc('/web/dataset/call_kw/res.users/language_switch', {
                model: 'res.users',
                method: 'language_switch',
                args: [user.userId],
                kwargs: { lang: selectedLang },
            });

            this.pos.reloadData();
//            window.location.reload();
        } catch (error) {
            await this.handleLanguageSwitchError();
        }
    },
//    /**
//     * Handles errors during the language switch process.
//     */
    async handleLanguageSwitchError() {
        const { popup } = this.env.services;
        this.dialog.add(AlertDialog, {
            title: _t("Error"),
            body: _t("Please try again."),
        });
    }
});
