/** Content of the modal: court booking, session registration and membership forms. */

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { Interaction } from "@web/public/interaction";
import { clearFieldError, formError, setLoading, validateForm } from "./forms";
import { getModal } from "./modal";
import { register } from "./services";
import { escapeHTML, formatDate, fromISODate, nextSessionDate } from "./utils";

/**
 * Submits the session and membership forms shown in the modal. Both become
 * CRM leads through the website route of the theme.
 */
export class AcModalForms extends Interaction {
    static selector = "#modalBody";
    dynamicContent = {
        _root: {
            "t-on-input": this.onInput,
            "t-on-submit": this.onSubmit,
        },
    };

    onInput(ev) {
        clearFieldError(ev);
    }

    async onSubmit(ev) {
        const form = ev.target.closest("form[data-form]");
        if (!form) {
            return;
        }
        ev.preventDefault();
        if (!validateForm(form)) {
            return;
        }
        const data = Object.fromEntries(new FormData(form));
        const button = form.querySelector('button[type="submit"]');
        setLoading(button, true, _t("Sending…"));
        try {
            if (form.dataset.form === "session") {
                await this.registerSession(form, data);
            } else if (form.dataset.form === "membership") {
                await this.registerMembership(form, data);
            }
        } catch (error) {
            formError(form, error.message);
        } finally {
            setLoading(button, false);
        }
    }

    async registerSession(form, data) {
        const { title, price, duration, priceText } = form.dataset;
        const next = nextSessionDate(data.sessionTime);
        const date = next?.date || "";
        const res = await this.waitFor(
            register("session", { sessionTitle: title, date, price: Number(price), ...data })
        );
        const when = date
            ? formatDate(fromISODate(date), { weekday: "long", day: "numeric", month: "long" })
            : data.sessionTime;
        getModal().showSuccess({
            title: _t("Request received."),
            text: _t(
                "Thanks, %(name)s! Your place in %(session)s is held for %(date)s. We will email you to confirm.",
                {
                    name: escapeHTML(data.name.split(" ")[0]),
                    session: escapeHTML(title),
                    date: escapeHTML(when),
                }
            ),
            reference: res.reference,
            details: [
                [_t("Session"), escapeHTML(title)],
                [_t("Time"), escapeHTML(data.sessionTime)],
                [_t("Duration"), escapeHTML(duration)],
                [_t("Price"), escapeHTML(priceText)],
            ],
            note: _t("Payment is taken at the club. Keep your reference to change or cancel the booking."),
        });
    }

    async registerMembership(form, data) {
        const res = await this.waitFor(register("membership", { plan: form.dataset.plan, ...data }));
        getModal().showSuccess({
            title: _t("Welcome to the club."),
            text: _t("Your %(plan)s application is in. Our team will be in touch at %(email)s.", {
                plan: escapeHTML(form.dataset.plan),
                email: escapeHTML(data.email),
            }),
            reference: res.reference,
        });
    }
}

registry.category("public.interactions").add("theme_aerocourt.modal_forms", AcModalForms);
