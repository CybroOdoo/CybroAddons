/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

/**
 * "Copy summary" on a meeting summary posted in a channel. Chat messages can't carry scripts or
 * buttons, so it is a link to the summary record, turned into a copy of the card's text here.
 */
export const meetingSummaryCopyService = {
    dependencies: ["notification"],
    start(env, { notification }) {
        // capture phase on the window: before any handler in the page, Discuss's included
        browser.addEventListener(
            "click",
            async (ev) => {
                const link = ev.target.closest?.(".o_meeting_summary_copy");
                const card = link?.closest(".o_meeting_summary_card");
                if (!card) {
                    return;
                }
                ev.preventDefault();
                ev.stopPropagation(); // before Discuss opens the link
                const text = card.innerText;
                const footer = card.querySelector(".o_meeting_summary_footer")?.innerText;
                const summary = (footer ? text.slice(0, text.lastIndexOf(footer)) : text).trim();
                try {
                    await browser.navigator.clipboard.writeText(summary);
                    notification.add(_t("Meeting summary copied."), { type: "success" });
                } catch {
                    notification.add(_t("Could not copy the meeting summary."), { type: "warning" });
                }
            },
            true
        );
    },
};

registry.category("services").add("discuss_meeting_ai.summary_copy", meetingSummaryCopyService);
