/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";
import { redirect } from "@web/core/utils/urls";
import { rpc } from "@web/core/network/rpc";

// ─────────────────────────────────────────────────────────────────────────────
// IP capture on the login form
// ─────────────────────────────────────────────────────────────────────────────
export class UserIpAddress extends Interaction {
    static selector = "form.oe_login_form, .oe_website_login_container";

    start() {
        this._getIpAddress();
    }

    async _getIpAddress() {
        try {
            const response = await fetch("https://api.ipify.org?format=json");
            if (response.ok) {
                const data = await response.json();
                const input = this.el.querySelector("#user_ip");
                if (input && data.ip) {
                    input.value = data.ip;
                }
            }
        } catch (e) {
            // Ignore network failure
        }
    }
}

registry
    .category("public.interactions")
    .add("geoip_website_redirect.user_ip", UserIpAddress);

// ─────────────────────────────────────────────────────────────────────────────
// Language switcher — also updates currency & pricelist
// ─────────────────────────────────────────────────────────────────────────────
export class GeoipLangChange extends Interaction {
    /**
     * We target the same ".js_change_lang" anchors that Odoo's own
     * LangChange interaction uses.  Because we register AFTER the built-in
     * one, we add our async currency call before letting the normal
     * redirect happen.
     */
    static selector = ".js_change_lang";

    dynamicContent = {
        _root: { "t-on-click.prevent": this.onLangClick },
    };

    async onLangClick(ev) {
        const el = ev.currentTarget;
        const urlCode = el.dataset.url_code || "";
        const href = el.getAttribute("href") || "";

        // Build the redirect URL exactly as Odoo's built-in interaction does
        const redirectURL = new URL(href, window.location.origin);
        redirectURL.searchParams.delete("edit_translations");
        const langParam = encodeURIComponent(urlCode);
        const rParam = encodeURIComponent(
            `${redirectURL.pathname}${redirectURL.search}`
        );
        const hash = encodeURIComponent(window.location.hash);
        const finalRedirect = `/website/lang/${langParam}?r=${rParam}${hash}`;

        // Fire & forget — tell the server to switch the pricelist for this lang.
        // We don't block navigation on failure.
        try {
            await rpc("/geoip/set_currency_by_lang", {
                lang_url_code: urlCode,
            });
        } catch (_e) {
            // Non-fatal; proceed with lang switch anyway
        }

        redirect(finalRedirect);
    }
}

registry
    .category("public.interactions")
    .add("geoip_website_redirect.lang_change", GeoipLangChange);
