import { Composer } from "@mail/core/common/composer";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { signal } from "@odoo/owl";

patch(Composer.prototype, {
    setup() {
        super.setup();
        this.autoCompleteRef = signal.ref(HTMLTextAreaElement);
        this.activeSuggestion = "";
        this._cachedSuggestions = null;
    },

    _getUserTextarea() {
        if (typeof this.ref === "function") {
            const el = this.ref();
            if (el) {
                return el;
            }
        }
        if (this.ref?.el) {
            return this.ref.el;
        }
        if (typeof this.rootRef === "function") {
            const root = this.rootRef();
            const el = root?.querySelector(".o-mail-Composer-input");
            if (el) {
                return el;
            }
        }
        return document.querySelector("#userInputText") || document.querySelector(".o-mail-Composer-input");
    },

    _getAutoCompleteTextarea() {
        if (typeof this.autoCompleteRef === "function") {
            const el = this.autoCompleteRef();
            if (el) {
                return el;
            }
        }
        if (this.autoCompleteRef?.el) {
            return this.autoCompleteRef.el;
        }
        if (typeof this.rootRef === "function") {
            const root = this.rootRef();
            const el = root?.querySelector(".ac-user-input--autocomplete");
            if (el) {
                return el;
            }
        }
        return document.querySelector("#autoCompleteText") || document.querySelector(".ac-user-input--autocomplete");
    },

    async _fetchSuggestions() {
        if (this._cachedSuggestions) {
            return this._cachedSuggestions;
        }
        const data = await rpc("/web/dataset/call_kw", {
            model: "mail.message",
            method: "get_message",
            args: [],
            kwargs: {},
        });
        this._cachedSuggestions = data || [];
        return this._cachedSuggestions;
    },

    onFocusin() {
        super.onFocusin?.(...arguments);
        this._cachedSuggestions = null;
    },

    async sendMessage() {
        this._cachedSuggestions = null;
        return super.sendMessage?.(...arguments);
    },

    onKeydown(ev) {
        const userTextEl = this._getUserTextarea();
        const autoCompleteEl = this._getAutoCompleteTextarea();
        const suggestion = this.activeSuggestion || (autoCompleteEl ? autoCompleteEl.value.trim() : "");

        if (ev.key === "Tab" || ev.key === "ArrowRight") {
            const hasSuggestion = Boolean(
                suggestion &&
                userTextEl &&
                suggestion.toLowerCase().startsWith(userTextEl.value.trim().toLowerCase())
            );
            if (hasSuggestion) {
                if (ev.key === "ArrowRight" && userTextEl.selectionStart !== userTextEl.value.length) {
                    super.onKeydown?.(ev);
                    return;
                }
                ev.preventDefault();
                userTextEl.value = suggestion;
                if (this.props?.composer) {
                    this.props.composer.composerText = suggestion;
                }
                if (autoCompleteEl) {
                    autoCompleteEl.value = "";
                }
                this.activeSuggestion = "";
                userTextEl.focus();
                return;
            }
        } else if (ev.key === "Enter" || ev.key === "Escape" || ev.key === " ") {
            if (autoCompleteEl) {
                autoCompleteEl.value = "";
            }
            this.activeSuggestion = "";
        }

        super.onKeydown?.(ev);
    },

    async onKeyupTextarea(ev) {
        const userTextEl = this._getUserTextarea();
        const autoCompleteEl = this._getAutoCompleteTextarea();
        if (!userTextEl || !autoCompleteEl) {
            return;
        }

        const value = userTextEl.value;
        if (!value.trim() || value === "/") {
            autoCompleteEl.value = "";
            this.activeSuggestion = "";
            return;
        }

        const searchTerms = await this._fetchSuggestions();
        if (!userTextEl.value.trim() || userTextEl.value === "/") {
            autoCompleteEl.value = "";
            this.activeSuggestion = "";
            return;
        }

        const escapedValue = userTextEl.value.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
        const matcher = new RegExp(`^${escapedValue}`, "i");
        const filterList = searchTerms.filter((word) => word && matcher.test(word));
        filterList.sort();

        if (filterList.length > 0) {
            autoCompleteEl.value = filterList[0];
            this.activeSuggestion = filterList[0];
        } else {
            autoCompleteEl.value = "";
            this.activeSuggestion = "";
        }
    },
});
