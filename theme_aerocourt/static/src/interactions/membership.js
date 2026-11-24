/** Membership plan buttons that open the join form. */

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { Interaction } from "@web/public/interaction";
import { fieldHTML, selectHTML } from "./forms";
import { getModal } from "./modal";
import { escapeHTML, money } from "./utils";

/** "Join" button of a membership plan: opens the application form in the modal. */
export class AcMembershipJoin extends Interaction {
    static selector = "[data-join]";
    dynamicContent = {
        _root: { "t-on-click": this.onClick },
    };

    onClick() {
        const plan = this.el.dataset.join;
        const price = Number(this.el.dataset.price);
        getModal().open(`
            <div class="ac-modal-content">
              <p class="ac-modal-sub">${_t("Membership")}</p>
              <h2 class="ac-modal-title" id="modalTitle" tabindex="-1">${_t("Join as %s", escapeHTML(plan))}</h2>
              <p class="ac-modal-lead">${price ? _t("%s per month. Cancel anytime with 30 days' notice.", money(price)) : _t("No monthly fee. Just pay for the courts you book.")}</p>
              <form class="ac-modal-form" data-form="membership" data-plan="${escapeHTML(plan)}" novalidate>
                <div class="ac-modal-form__grid">
                  ${fieldHTML({ name: "name", label: _t("Full name"), autocomplete: "name" })}
                  ${fieldHTML({ name: "email", label: _t("Email"), type: "email", autocomplete: "email", placeholder: "you@example.com" })}
                  ${fieldHTML({ name: "phone", label: _t("Phone"), type: "tel", required: false, autocomplete: "tel" })}
                  ${selectHTML({ name: "start", label: _t("Start"), options: [_t("This month"), _t("Next month")] })}
                </div>
                <div class="ac-modal-actions">
                  <button type="submit" class="ac-btn ac-btn--primary"><span class="ac-btn__label">${_t("Submit application")}</span> <i class="ac-icon ac-i-ph-arrow-right-bold" aria-hidden="true"></i></button>
                  <button type="button" class="ac-btn ac-btn--ghost" data-modal-close>${_t("Cancel")}</button>
                </div>
                <p class="ac-modal-note"><i class="ac-icon ac-i-ph-info-bold" aria-hidden="true"></i> ${_t("Our team will contact you to finish your membership.")}</p>
              </form>
            </div>`);
    }
}

registry.category("public.interactions").add("theme_aerocourt.membership_join", AcMembershipJoin);
