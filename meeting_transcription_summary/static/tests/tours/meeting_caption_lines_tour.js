/** @odoo-module **/
import { registry } from "@web/core/registry";

// A participant other than the one running the tour: their captions arrive over the bus.
const SPEAKER = { member_id: 999999, partner_id: 999999, partner_name: "Bob" };

function speech() {
    return odoo.__WOWL_DEBUG__.root.env.services["discuss_meeting_ai.speech"];
}

function caption(text) {
    // what the bus subscription hands over for "discuss.channel/meeting_subtitle"
    speech().handleIncomingSubtitle({ ...SPEAKER, text });
}

function shownCaptions() {
    return [...document.querySelectorAll(".o-meeting-subtitle-text")].map((el) => el.textContent.trim());
}

function expectCaptions(expected) {
    const shown = shownCaptions();
    if (JSON.stringify(shown) !== JSON.stringify(expected)) {
        throw new Error(`Captions shown: ${JSON.stringify(shown)}, expected ${JSON.stringify(expected)}`);
    }
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

registry.category("web_tour.tours").add("meeting_transcription_summary.caption_lines", {
    steps: () => [
        { trigger: ".o-discuss-Call button[title='Disconnect']" },
        {
            content: "Turn on Subtitle(CC)",
            trigger: ".o-discuss-Call",
            async run() {
                const store = odoo.__WOWL_DEBUG__.root.env.services["mail.store"];
                await speech().toggleSubtitles(store.rtc.channel);
                caption("First caption.");
            },
        },
        {
            content: "The next caption goes under the first one, which stays",
            trigger: ".o-meeting-subtitle-text:contains('First caption.')",
            async run() {
                await sleep(1000);
                caption("Second caption.");
                await sleep(100);
                expectCaptions(["First caption.", "Second caption."]);
            },
        },
        {
            content: "At most three lines: the oldest goes first",
            trigger: ".o-meeting-subtitle-text:contains('Second caption.')",
            async run() {
                caption("Third caption.");
                caption("Fourth caption.");
                await sleep(100);
                expectCaptions(["Second caption.", "Third caption.", "Fourth caption."]);
            },
        },
        {
            content: "Each line stays six seconds, then goes",
            trigger: ".o-meeting-subtitle-text:contains('Fourth caption.')",
            async run() {
                await sleep(4000); // the first lines were shown about 1 s ago
                expectCaptions(["Second caption.", "Third caption.", "Fourth caption."]);
                await sleep(2500);
                expectCaptions([]);
            },
        },
        {
            content: "A lost caption is explained once, in a notification that closes by itself",
            trigger: ".o-discuss-Call",
            async run() {
                const reason = "Captions skipped: api.groq.com allows no more requests this minute.";
                speech().notifyCaptionError(reason);
                speech().notifyCaptionError(reason); // the next lost caption, right after
                await sleep(100);
                const shown = [...document.querySelectorAll(".o_notification")].filter((el) =>
                    el.textContent.includes(reason)
                );
                if (shown.length !== 1) {
                    throw new Error(`The reason is shown ${shown.length} times, expected once`);
                }
            },
        },
        {
            content: "...and closes by itself",
            trigger: "body:not(:has(.o_notification:contains('allows no more requests')))",
            timeout: 15000,
        },
    ],
});
