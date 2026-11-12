import {
    click,
    contains,
    defineMailModels,
    inputFiles,
    insertText,
    mockGetMedia,
    openDiscuss,
    start,
    startServer,
} from "@mail/../tests/mail_test_helpers";
import { describe, expect, getFixture, test, waitUntil } from "@odoo/hoot";
import { mockService, onRpc, patchWithCleanup } from "@web/../tests/web_test_helpers";
import { browser } from "@web/core/browser/browser";

import {
    meetingSubtitlesAction,
    meetingSummaryAction,
    meetingTranscribeAction,
} from "@meeting_transcription_summary/discuss/call/call_actions_patch";
import { MeetingSummaryDialog } from "@meeting_transcription_summary/discuss/call/meeting_summary_dialog";
import { UploadRecordingDialog } from "@meeting_transcription_summary/discuss/upload/upload_recording_dialog";

describe.current.tags("desktop");
defineMailModels();

/** Notifications recorded as steps. */
function recordNotifications() {
    mockService("notification", {
        add(message, { type } = {}) {
            expect.step(`${type}: ${message}`);
            return () => {};
        },
    });
}

describe("call actions", () => {
    test("the three meeting actions in a call", async () => {
        const pyEnv = await startServer();
        mockGetMedia();
        const channelId = pyEnv["discuss.channel"].create({ name: "Ops Review" });
        onRpc("/discuss/meeting/state", () => ({ channel_id: channelId, transcribe: false, subtitles: false }));
        onRpc("/discuss/meeting/set_subtitles", async (request) => {
            const { params } = await request.json();
            expect.step(`subtitles ${params.enabled}`);
            return { channel_id: channelId, transcribe: false, subtitles: params.enabled };
        });
        onRpc("/discuss/meeting/transcript", () => ({ transcribe: false, lines: [] }));
        const env = await start();
        const speech = env.services["discuss_meeting_ai.speech"];
        patchWithCleanup(speech, { startAudioCapture() {} });
        await openDiscuss(channelId);
        await click("[title='Start Call']");
        await contains(".o-discuss-Call");
        await click("[title='More']");
        await contains(".o-dropdown-item:contains('Subtitle(CC): Off')");
        await contains(".o-dropdown-item:contains('Transcribe')");
        await click(".o-dropdown-item:contains('Subtitle(CC): Off')");
        await waitUntil(() => speech.state.subtitlesEnabled);
        expect.verifySteps(["subtitles true"]);
        // captions and the badge are shown over the call
        await contains(".o-meeting-status-badge:contains('CC On')");
        speech.updateActiveSubtitle({ id: "remote-member-1", speaker: "Bob", text: "Hello everyone." });
        await contains(".o-meeting-subtitle-bubble:contains('Hello everyone.')");
        await contains(".o-meeting-speaker-badge:contains('Bob')");
        await click("[title='More']");
        await click(".o-dropdown-item:contains('AI Summary & Notes')");
        await contains(".o-meeting-summary-modal");
    });

    test("joining and leaving a call", async () => {
        const pyEnv = await startServer();
        mockGetMedia();
        const channelId = pyEnv["discuss.channel"].create({ name: "Ops Review" });
        onRpc("/discuss/meeting/state", () => ({ channel_id: channelId, transcribe: true, subtitles: false }));
        const env = await start();
        const speech = env.services["discuss_meeting_ai.speech"];
        patchWithCleanup(speech, { startAudioCapture() {} });
        await openDiscuss(channelId);
        await click("[title='Start Call']");
        // the call's state is picked up on joining
        await waitUntil(() => speech.state.transcribeEnabled);
        expect(speech.state.activeChannelId).toBe(channelId);
        await contains(".o-meeting-status-badge:contains('Transcribing')");
        await click(".o-discuss-CallActionList button[aria-label='Disconnect']");
        await contains(".o-discuss-Call", { count: 0 });
        expect(speech.state.activeChannelId).toBe(null, { message: "leaving resets the meeting" });
        expect(speech.state.transcribeEnabled).toBe(false);
    });

    test("conditions and labels", async () => {
        await startServer();
        await start(); // labels are translated
        const speech = { state: { subtitlesEnabled: true, transcribeEnabled: false } };
        const store = { env: { services: { "discuss_meeting_ai.speech": speech } } };
        const internal = { ...store, self_partner: { main_user_id: { share: false } } };
        const portal = { ...store, self_partner: { main_user_id: { share: true } } };
        const inCall = { isSelfInCall: true };
        expect(meetingSubtitlesAction.condition({ store: portal, thread: inCall })).toBe(true);
        expect(meetingSubtitlesAction.condition({ store: portal, thread: { isSelfInCall: false } })).toBe(false);
        expect(meetingTranscribeAction.condition({ store: internal, thread: inCall })).toBe(true);
        expect(meetingTranscribeAction.condition({ store: portal, thread: inCall })).toBe(false,
            { message: "guests and portal users can't transcribe a call" });
        expect(meetingSummaryAction.condition({ store: portal, thread: inCall })).toBe(false);
        expect(String(meetingSubtitlesAction.name({ store }))).toBe("Subtitle(CC): On");
        expect(meetingSubtitlesAction.isActive({ store })).toBe(true);
        expect(String(meetingTranscribeAction.name({ store }))).toBe("Transcribe");
        speech.state.transcribeEnabled = true;
        expect(String(meetingTranscribeAction.name({ store }))).toBe("Stop Transcribing");
        expect(meetingTranscribeAction.tags({ action: { isActive: true } })).toHaveLength(1);
        expect(meetingTranscribeAction.tags({ action: { isActive: false } })).toEqual([]);
        // the speech service may also come from the component's env
        const owner = { env: { services: { "discuss_meeting_ai.speech": speech } } };
        expect(meetingSubtitlesAction.isActive({ owner })).toBe(true);
        expect(meetingSubtitlesAction.isActive({})).toBe(false);
    });
});

describe("summary dialog", () => {
    const lines = [
        { id: 1, time: "10:00:01", speaker: "Alice", text: "We will ship on Monday." },
        { id: 2, time: "10:00:05", speaker: "Bob", text: "Agreed." },
    ];

    async function openSummaryDialog(channelId) {
        const env = await start();
        env.services.dialog.add(MeetingSummaryDialog, { channel: { id: channelId } });
        await contains(".o-meeting-summary-modal");
        return env;
    }

    test("transcript, summary and posting", async () => {
        const pyEnv = await startServer();
        const channelId = pyEnv["discuss.channel"].create({ name: "Ops Review" });
        recordNotifications();
        onRpc("/discuss/meeting/transcript", () => ({ transcribe: true, lines }));
        onRpc("/discuss/meeting/summarize", () => ({
            status: "success",
            summary_id: 7,
            title: "Meeting: Ops Review",
            executive_summary: "<p>The team <strong>agreed</strong> to ship.</p>",
            key_discussion_points: "Alice: Shipping.",
            decisions: "Bob: Agreed.",
            action_items: "Alice: Will ship on Monday.",
        }));
        onRpc("/discuss/meeting/post_summary", async (request) => {
            const { params } = await request.json();
            expect.step(`post ${params.summary_id}`);
            return { status: "posted" };
        });
        patchWithCleanup(navigator.clipboard, { writeText: async (text) => expect.step(text) });
        await openSummaryDialog(channelId);
        await click("button:contains('Meeting Transcript')");
        await contains("button:contains('Meeting Transcript') .badge:contains('2')");
        await contains(".modal span:contains('We will ship on Monday.')");
        await click("button:contains('Copy')");
        expect.verifySteps([
            "[10:00:01] Alice: We will ship on Monday.\n[10:00:05] Bob: Agreed.",
            "info: Transcript copied to clipboard!",
        ]);
        await click("button:contains('AI Summary')");
        await click(".modal-footer button:contains('Generate Summary')");
        await contains(".o-summary-result strong:contains('agreed')", { message: "rendered as HTML" });
        await contains(".o-summary-result:contains('Alice: Will ship on Monday.')");
        await contains(".modal-footer button:contains('Refresh Summary')");
        expect.verifySteps(["success: AI Meeting Summary successfully generated!"]);
        await click(".modal-footer button:contains('Post to Channel Chatter')");
        await contains(".modal-footer button:contains('Posted to Chat'):disabled");
        expect.verifySteps(["post 7", "success: Meeting summary posted to the channel chatter!"]);
    });

    test("nothing recorded yet", async () => {
        const pyEnv = await startServer();
        const channelId = pyEnv["discuss.channel"].create({ name: "Ops Review" });
        recordNotifications();
        onRpc("/discuss/meeting/transcript", () => ({ transcribe: false, lines: [] }));
        onRpc("/discuss/meeting/summarize", () => ({
            error: "Nothing has been transcribed in this call yet.",
        }));
        patchWithCleanup(navigator.clipboard, { writeText: async () => expect.step("copied") });
        await openSummaryDialog(channelId);
        await click("button:contains('Meeting Transcript')");
        await contains(".modal p:contains('Nothing recorded yet.')");
        await click(".modal-footer button:contains('Generate Summary')");
        await expect.waitForSteps(["warning: Nothing has been transcribed in this call yet."]);
        await contains(".modal-footer button:contains('Post to Channel Chatter')", { count: 0 });
    });

    test("transcribing, but nothing said yet", async () => {
        const pyEnv = await startServer();
        const channelId = pyEnv["discuss.channel"].create({ name: "Ops Review" });
        onRpc("/discuss/meeting/transcript", () => ({ transcribe: true, lines: [] }));
        await openSummaryDialog(channelId);
        await click("button:contains('Meeting Transcript')");
        await contains(".modal p:contains('Transcribing: nothing has been said yet.')");
    });

    test("server failures", async () => {
        const pyEnv = await startServer();
        const channelId = pyEnv["discuss.channel"].create({ name: "Ops Review" });
        recordNotifications();
        let transcriptCalls = 0;
        onRpc("/discuss/meeting/transcript", () => {
            if (transcriptCalls++ === 0) {
                throw new Error("offline");
            }
            return { error: "not_in_call" };
        });
        onRpc("/discuss/meeting/summarize", () => ({ status: "success", summary_id: 7 }));
        let postCalls = 0;
        onRpc("/discuss/meeting/post_summary", () => {
            if (postCalls++ === 0) {
                return { error: "This summary has already been posted to the channel." };
            }
            throw new Error("offline");
        });
        patchWithCleanup(console, { error: () => expect.step("logged") });
        await openSummaryDialog(channelId); // the transcript failed to load: still opens
        await click(".modal-footer button:contains('Generate Summary')");
        await contains(".modal-footer button:contains('Post to Channel Chatter')");
        expect.verifySteps(["success: AI Meeting Summary successfully generated!"]);
        await click(".modal-footer button:contains('Post to Channel Chatter')");
        await waitUntil(() => postCalls === 1);
        await contains(".modal-footer button:contains('Post to Channel Chatter'):enabled");
        expect.verifySteps(["warning: This summary has already been posted to the channel."]);
        await click(".modal-footer button:contains('Post to Channel Chatter')");
        await waitUntil(() => postCalls === 2);
        await expect.waitForSteps(["logged", "danger: Could not post summary to channel."]);
    });

    test("summarizing fails", async () => {
        const pyEnv = await startServer();
        const channelId = pyEnv["discuss.channel"].create({ name: "Ops Review" });
        recordNotifications();
        onRpc("/discuss/meeting/transcript", () => ({ transcribe: true, lines }));
        onRpc("/discuss/meeting/summarize", () => {
            throw new Error("timeout");
        });
        patchWithCleanup(console, { error: () => expect.step("logged") });
        await openSummaryDialog(channelId);
        await click(".modal-footer button:contains('Generate Summary')");
        await expect.waitForSteps(["logged", "danger: Failed to contact summarization service."]);
        await contains(".modal-footer button:contains('Generate Summary'):enabled");
    });
});

describe("upload recording dialog", () => {
    async function openUploadDialog(name = "Ops Review") {
        const pyEnv = await startServer();
        const channelId = pyEnv["discuss.channel"].create({ name });
        const env = await start();
        env.services.dialog.add(UploadRecordingDialog, { thread: { id: channelId, displayName: name } });
        await contains(".modal input[type=file]");
        return { env, channelId };
    }

    const recording = () => new File(["ID3 fake audio"], "board.mp3", { type: "audio/mpeg" });

    test("upload, then open the summary", async () => {
        recordNotifications();
        onRpc("/discuss/meeting/upload_recording", async (request) => {
            const form = await request.formData();
            expect.step(`${form.get("title")} / ${form.get("duration_minutes")} / ${form.get("file").name}`);
            return { status: "success", summary_id: 9, message: "Recording uploaded." };
        });
        const { env, channelId } = await openUploadDialog();
        patchWithCleanup(env.services.action, {
            doAction(action) {
                expect.step(`open ${action.res_model} ${action.res_id}`);
            },
        });
        await contains(".modal-footer button:contains('Transcribe & Post Summary'):disabled",
            { message: "nothing to upload yet" });
        await contains(`.modal input[type=text]`);
        expect(document.querySelector(".modal input[type=text]").value).toMatch(/^Recording: Ops Review \(/);
        await inputFiles(".modal input[type=file]", [recording()]);
        await insertText(".modal input[type=text]", "Board meeting", { replace: true });
        await click(".modal-footer button:contains('Transcribe & Post Summary')");
        await contains(".modal .alert-success:contains('Recording uploaded.')");
        expect.verifySteps([
            "Board meeting / 15 / board.mp3",
            "info: Recording uploaded: the summary will be posted to #Ops Review once it is transcribed.",
        ]);
        expect(channelId).toBeGreaterThan(0);
        await click(".modal button:contains('View Summary Record')");
        await expect.waitForSteps(["open discuss.meeting.summary 9"]);
    });

    test("refused by the server", async () => {
        onRpc("/discuss/meeting/upload_recording", () => ({ status: "error", error: "Channel not found" }));
        await openUploadDialog();
        await inputFiles(".modal input[type=file]", [recording()]);
        await click(".modal-footer button:contains('Transcribe & Post Summary')");
        await contains(".modal .alert-danger:contains('Channel not found')");
    });

    test("server error", async () => {
        onRpc("/discuss/meeting/upload_recording", () => new Response("", { status: 413, statusText: "Too Large" }));
        patchWithCleanup(console, { error: () => expect.step("logged") });
        await openUploadDialog();
        await inputFiles(".modal input[type=file]", [recording()]);
        await click(".modal-footer button:contains('Transcribe & Post Summary')");
        await contains(".modal .alert-danger:contains('Server error (413)')");
        expect.verifySteps(["logged"]);
        await contains(".modal-footer button:contains('Transcribe & Post Summary'):enabled",
            { message: "can be tried again" });
    });

    test("thread action in a channel, for internal users", async () => {
        const pyEnv = await startServer();
        const channelId = pyEnv["discuss.channel"].create({ name: "Ops Review" });
        await start();
        await openDiscuss(channelId);
        await click(".o-mail-DiscussContent-header button[title='Upload Meeting Recording'], " +
            "[title='Upload Meeting Recording']");
        await contains(".modal:contains('Upload Meeting Recording') input[type=file]");
    });
});

describe("copy summary link", () => {
    test("a long summary scrolls; the copy still takes all of it", async () => {
        recordNotifications();
        await start();
        let copied;
        patchWithCleanup(browser.navigator.clipboard, { writeText: async (text) => (copied = text) });
        const card = document.createElement("div");
        card.className = "o_meeting_summary_card";
        const items = Array.from({ length: 60 }, (_, i) => `<li>Point ${i + 1}</li>`).join("");
        card.innerHTML = `<h3>Weekly review</h3>
            <div class="o_meeting_summary_body"><ul>${items}</ul></div>
            <div class="o_meeting_summary_footer">
            <a href="/odoo/discuss.meeting.summary/1" class="o_meeting_summary_copy">Copy summary</a></div>`;
        getFixture().appendChild(card);
        try {
            const body = card.querySelector(".o_meeting_summary_body");
            expect(getComputedStyle(body).maxHeight).toBe("420px");
            expect(getComputedStyle(body).overflowY).toBe("auto");
            expect(body.scrollHeight).toBeGreaterThan(body.clientHeight);
            await click(".o_meeting_summary_copy");
            await waitUntil(() => copied);
            expect(copied).toMatch(/Point 1\s/);
            expect(copied).toMatch(/Point 60$/, { message: "scrolled-out text is copied too" });
            expect.verifySteps(["success: Meeting summary copied."]);
        } finally {
            card.remove();
        }
    });

    test("copies the card's text without its footer", async () => {
        recordNotifications();
        await start();
        let copied;
        patchWithCleanup(browser.navigator.clipboard, { writeText: async (text) => (copied = text) });
        const card = document.createElement("div");
        card.className = "o_meeting_summary_card";
        card.innerHTML = `<h3>Weekly review</h3><p>We agreed to ship.</p>
            <div class="o_meeting_summary_footer">Posted by OdooBot
            <a href="/odoo/discuss.meeting.summary/1" class="o_meeting_summary_copy">Copy summary</a></div>`;
        getFixture().appendChild(card);
        try {
            await click(".o_meeting_summary_copy");
            await waitUntil(() => copied);
            expect(copied).toMatch(/^Weekly review\s+We agreed to ship\.$/);
            expect.verifySteps(["success: Meeting summary copied."]);
            patchWithCleanup(browser.navigator.clipboard, { writeText: async () => {
                throw new Error("denied");
            } });
            await click(".o_meeting_summary_copy");
            await expect.waitForSteps(["warning: Could not copy the meeting summary."]);
        } finally {
            card.remove();
        }
    });
});
