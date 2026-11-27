/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { SurveyForm } from "@survey/interactions/survey_form";

patch(SurveyForm.prototype, {
    start() {
        super.start();
        this.addListener(this.el, "focusin", (ev) => {
            if (ev.target.matches(".o_select_Country")) {
                this._onSelectCountry(ev);
            }
        });
        this.addListener(this.el, "change", (ev) => {
            if (ev.target.matches(".o_select_Country")) {
                this._onSelectState(ev);
            } else if (ev.target.matches(".o_select_many2many")) {
                this._onSelectMany2many(ev);
            }
        });
    },

    _onSelectCountry(ev) {
        const select = ev.target;
        rpc("/survey/load_country").then((result) => {
            select.replaceChildren(new Option(_t("Country"), ""));
            if (result && result.name) {
                result.name.forEach((countryName) => {
                    select.add(new Option(countryName, countryName));
                });
            }
        });
    },

    _onSelectState(ev) {
        const country = ev.target.value;
        const qid = ev.target.dataset.id;

        rpc("/survey/load_states", {
            country_id: country,
        }).then((result) => {
            const stateSelect = this.el.querySelector(
                `#${CSS.escape(`${qid}-state`)}`
            );
            if (!stateSelect) {
                return;
            }
            stateSelect.replaceChildren(new Option(_t("State"), ""));
            if (result && result.name) {
                result.name.forEach((stateName) => {
                    stateSelect.add(new Option(stateName, stateName));
                });
            }
        });
    },

    _onSelectMany2many(ev) {
        const source = ev?.target || this.el.querySelector(".o_select_many2many");
        if (!source) {
            return;
        }
        const wrapper = source.closest(".oe_empty");
        const target =
            wrapper?.querySelector(".o_select_many2many_text") ||
            (source.name ? this.el.querySelector(`.${CSS.escape(source.name)}`) : null);
        if (target) {
            target.value = Array.from(source.selectedOptions)
                .map((opt) => opt.value)
                .filter(Boolean)
                .join(", ");
        }
    },
});
