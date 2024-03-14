/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { jsonrpc } from "@web/core/network/rpc_service";
/**
 * OrderlineLanguageSwitchButton is a component responsible for switching the user's preferred language.
 */
export class OrderlineLanguageSwitchButton extends Component {
    /**
     * The Owl template for the component.
     */
    static template = "point_of_sale.LanguageChange";
    /**
     * Setup function to initialize the component.
     */
    setup() {
        const { popup, user } = this.env.services;
        const pos = useService("pos");
        this.popup = popup;
        this.availLang = pos.langs;
        this.orm = useService("orm");
        this.userId = pos.user.id;
        this.curLang = user.lang;
    }
    /**
     * Click event handler for the language switch button.
     */
    async onClick() {
        const availableLang = this.availLang
            .filter(lang => lang.code !== this.curLang)
            .map(lang => ({
                id: lang.id,
                label: lang.name,
                item: lang.code,
            }));
        const { confirmed, payload: selectedLang } = await this.popup.add(SelectionPopup, {
            title: _t('Available Languages'),
            list: availableLang,
        });
        if (confirmed) {
            await this.handleLanguageSwitch(selectedLang);
        }
    }
    /**
     * Handles the language switch process.
     *
     * @param {string} selectedLang - The selected language code.
     */
    async handleLanguageSwitch(selectedLang) {
        try {
            await jsonrpc('/web/dataset/call_kw/res.users/language_switch', {
                model: 'res.users',
                method: 'language_switch',
                args: [this.userId],
                kwargs: { lang: selectedLang },
            });

            await jsonrpc("/web/session/get_session_info");
            window.location.reload();
        } catch (error) {
            await this.handleLanguageSwitchError();
        }
    }
    /**
     * Handles errors during the language switch process.
     */
    async handleLanguageSwitchError() {
        const { popup } = this.env.services;
        await popup.add(ErrorPopup, {
            title: _t("Error"),
            body: _t("Please try again."),
        });
    }
}
/**
 * Add the OrderlineLanguageSwitchButton component to the control buttons in the ProductScreen.
 */
ProductScreen.addControlButton({
    component: OrderlineLanguageSwitchButton,
});
