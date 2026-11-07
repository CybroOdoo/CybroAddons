/** @odoo-module **/
import {Counter} from "@backend_theme_infinito/js/editor_menu";
import {onPatched} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {rpc} from "@web/core/network/rpc";
import {session} from "@web/session";
import {useService} from "@web/core/utils/hooks";
import {applyAnimation} from "./animation";
import {getFontNameFromUrl} from "./font_utils";
import {GoogleFontDialog} from "./GoogleFontDialog";
import {OTHER_TOGGLES, SYNCED_TOGGLES, syncTogglesToSession} from "./toggle_utils";

export class Sidebar extends Counter {
    static template = "backend_theme_infinito_plus.Sidebar";

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this.session = session;
        this.chatBoxPosition = [
            {value: "Top Right", label: _t("Top Right")},
            {value: "Top Left", label: _t("Top Left")},
            {value: "Bottom Right", label: _t("Bottom Right")},
            {value: "Bottom Left", label: _t("Bottom Left")},
        ];
        this.infinitoAnimation = [
            {value: "Default", label: _t("Default")},
            {value: "Scale", label: _t("Scale")},
            {value: "Slide in", label: _t("Slide in")},
        ];
        this.font_id = parseInt(session.infinitoGoogleFont) || 0;
        // Toggles changed by the user and not saved yet (element id -> checked)
        this.changedToggles = {};
        this.renderData();

        onPatched(() => {
            for (const [id, key] of Object.entries({...SYNCED_TOGGLES, ...OTHER_TOGGLES})) {
                const el = document.getElementById(id);
                if (el) {
                    // Keep what the user already toggled when the sidebar re-renders
                    el.checked = id in this.changedToggles
                        ? this.changedToggles[id]
                        : !!session[key];
                }
            }
            const setValue = (sel, val) => {
                const el = document.querySelector(sel);
                if (el) {
                    el.value = val;
                }
            };
            setValue("#chatterbox_position", session.chatBoxPosition || "Top Right");
            setValue("#animated_view", session.infinitoAnimation || "Default");
            setValue("#infinito_font_select", String(session.infinitoGoogleFont || "System Font"));
        });
    }

    /** Remembers every toggle the user changes so it can be saved. */
    onToggleChange(ev) {
        const id = ev.target.id;
        if (id in SYNCED_TOGGLES || id === "navbarRefreshToggler") {
            this.changedToggles[id] = ev.target.checked;
        }
    }

    /**
     * Loads the loader list (base class, if it still has renderData)
     * and the list of Google fonts.
     */
    async renderData() {
        if (typeof super.renderData === "function") {
            await super.renderData(...arguments);
        }
        this.state.fontData = await this.orm.searchRead("infinito.google.font", [], ["name"]);
    }

    /**
     * Replacement for t-model on the loader select: store the value,
     * then run the base handler.
     */
    onLoaderSelect(ev) {
        this.state.loader = ev.target.value;
        if (typeof this.onLoaderChange === "function") {
            return this.onLoaderChange(ev);
        }
    }

    /** Previews the selected animation. */
    onAnimationChange(ev) {
        applyAnimation(ev.target.value);
    }

    _removeFontPreview() {
        document.getElementById("infinito-font-preview")?.remove();
    }

    /**
     * Previews a font family with an injected <style> tag.
     * @param {string|null} fontName - Font to preview, or null for the system font.
     */
    _applyFont(fontName) {
        this._removeFontPreview();
        const family = fontName
            ? `'${fontName.replace(/['"\\;{}]/g, "")}', sans-serif`
            : `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`;
        const styleEl = document.createElement("style");
        styleEl.id = "infinito-font-preview";
        styleEl.textContent = `
            * { font-family: ${family} !important; }
            .oi { font-family: 'odoo_ui_icons' !important; }
        `;
        document.head.appendChild(styleEl);
    }

    /** Previews the selected font and stores its id for saving. */
    onFontChange(ev) {
        const options = ev.target.options;
        const selected = options[options.selectedIndex];
        if (selected.classList.contains("add-font")) {
            this.OpenModal();
            return;
        }
        if (selected.classList.contains("system-font")) {
            this.font_id = 0;
            this._applyFont(null);
        } else {
            this.font_id = parseInt(selected.dataset.id) || 0;
            this._applyFont(selected.text.trim());
        }
    }

    /** Opens the dialog used to add a Google Font. */
    OpenModal() {
        this.dialog.add(
            GoogleFontDialog,
            {save: (url) => this._onSaveGoogleFont(url)},
            {onClose: () => this._resetFontSelect()}
        );
    }

    /** Puts the font select back on the current font after the dialog is closed. */
    _resetFontSelect() {
        const select = document.getElementById("infinito_font_select");
        if (select) {
            select.value = String(this.font_id || "System Font");
        }
    }

    /**
     * Saves the Google Font entered in the dialog and reloads the page.
     * @returns {Promise<boolean>} false when the font was not saved.
     */
    async _onSaveGoogleFont(url) {
        url = (url || "").trim();
        if (!url) {
            return false;
        }
        const fontName = getFontNameFromUrl(url);
        if (!fontName) {
            this.notification.add(
                _t("Could not detect a Google Font name from that URL."),
                {type: "danger"});
            return false;
        }
        try {
            await this.orm.call("infinito.google.font", "save_google_fonts", [[fontName, url]]);
        } catch (error) {
            this.notification.add(
                error?.data?.message || error?.message || _t("Failed to save the Google Font."),
                {type: "danger"});
            return false;
        }
        window.location.reload();
        return true;
    }

    /** Close button: undo previews, run the base close, then ask the menu to unmount. */
    _onCloseClick(ev) {
        this._removeFontPreview();
        applyAnimation(session.infinitoAnimation);
        const baseClose = this._Close_changes || this.closeSidebar;
        if (typeof baseClose === "function") {
            baseClose.call(this, ev);
        }
        document.dispatchEvent(new CustomEvent("infinito-plus-close"));
    }

    /**
     * Saves the Infinito Plus options, then lets the base method save the
     * other options. The page is reloaded at the end so the new font,
     * chatbox position and animation are applied.
     */
    async _SaveChanges() {
        const vals = {
            infinitoRefresh: document.querySelector("#navbarRefreshToggler").checked,
            infinitoGoogleFont: this.font_id,
            chatBoxPosition: document.querySelector("#chatterbox_position").value,
            infinitoAnimation: document.querySelector("#animated_view").value,
        };
        try {
            await rpc("/theme_studio/set_advanced_data_plus", {args: [{vals}]});
        } catch (error) {
            this.notification.add(
                error?.data?.message || error?.message || _t("Could not save the settings."),
                {type: "danger"});
            return;
        }
        // The base _SaveChanges saves the values stored in the session
        syncTogglesToSession(session, this.changedToggles);
        if (typeof super._SaveChanges === "function") {
            await super._SaveChanges(...arguments);
        }
        window.location.reload();
    }
}