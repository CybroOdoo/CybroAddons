import { waitNotifications } from "@bus/../tests/bus_test_helpers";
import { defineMailModels, start, startServer } from "@mail/../tests/mail_test_helpers";
import { advanceTime, beforeEach, describe, expect, test, waitUntil } from "@odoo/hoot";
import { onRpc, patchWithCleanup, serverState } from "@web/../tests/web_test_helpers";

describe.current.tags("desktop");
defineMailModels();

const RATE = 16000;
const BLOCK = 2048; // what the capture worklet posts: 0.128 s at 16 kHz

const silence = () => new Float32Array(BLOCK);
const voice = (level = 0.1) => new Float32Array(BLOCK).fill(level);

let channelId, pyEnv;
beforeEach(async () => {
    pyEnv = await startServer();
    channelId = pyEnv["discuss.channel"].create({ name: "Ops Review" });
});

/** The speech service of a started client, its notifications recorded as steps. */
async function startSpeech() {
    const env = await start();
    const speech = env.services["discuss_meeting_ai.speech"];
    patchWithCleanup(speech.notification, {
        add(message) {
            expect.step(String(message));
        },
    });
    return speech;
}

/** Capture "started" without a microphone: only what the service does around it is tested. */
function fakeCapture(speech) {
    patchWithCleanup(speech, {
        startAudioCapture() {
            this.state.isStreamingAudio = true;
            expect.step("capture started");
        },
        stopCapture() {
            if (this.state.isStreamingAudio) {
                expect.step("capture stopped");
            }
            this.state.isStreamingAudio = false;
        },
    });
}

describe("captions on screen", () => {
    test("at most three lines, each kept six seconds", async () => {
        const speech = await startSpeech();
        for (const text of ["one", "two", "three", "four"]) {
            speech.updateActiveSubtitle({ id: "local-user", speaker: "Alice", text });
        }
        expect(speech.state.activeSubtitles.map((s) => s.text)).toEqual(["two", "three", "four"]);
        expect(new Set(speech.state.activeSubtitles.map((s) => s.id)).size).toBe(3);
        await advanceTime(5000);
        expect(speech.state.activeSubtitles).toHaveLength(3);
        await advanceTime(1100);
        expect(speech.state.activeSubtitles).toHaveLength(0);
    });

    test("a caption without a speaker name", async () => {
        const speech = await startSpeech();
        speech.updateActiveSubtitle({ id: "x", text: "Hello" });
        expect(speech.state.activeSubtitles[0].speaker).toBe("Speaker");
        expect(speech.state.activeSubtitles[0].time).toMatch(/\d/);
    });

    test("other participants' captions are shown, our own are not repeated", async () => {
        const speech = await startSpeech();
        speech.handleIncomingSubtitle({ member_id: 42, partner_name: "Bob", text: "Hi", time: "10:00:01" });
        speech.handleIncomingSubtitle({ partner_id: 999, partner_name: "Carol", text: "Hello" });
        speech.handleIncomingSubtitle({ partner_name: "Visitor", text: "Hey" });
        const selfPartnerId = speech.store.self_partner.id;
        speech.handleIncomingSubtitle({ partner_id: selfPartnerId, partner_name: "Me", text: "Mine" });
        const shown = speech.state.activeSubtitles;
        expect(shown.map((s) => s.text)).toEqual(["Hi", "Hello", "Hey"]);
        expect(shown[0].id).toMatch(/^remote-member-42-/);
        expect(shown[0].time).toBe("10:00:01");
        expect(shown[1].id).toMatch(/^remote-999-/);
        expect(shown[2].id).toMatch(/^remote-guest-/, { message: "guests are told apart by member" });
    });
});

describe("bus notifications", () => {
    /** Send ``payload`` to this user over the (mock) bus, as the server does. */
    const send = (type, payload) => pyEnv["bus.bus"]._sendone(serverState.partnerId, type, payload);

    test("captions of the call are shown while watching subtitles", async () => {
        const speech = await startSpeech();
        speech.state.activeChannelId = channelId;
        const caption = { channel_id: channelId, member_id: 42, partner_name: "Bob", text: "Hello." };
        send("discuss.channel/meeting_subtitle", caption);
        await waitNotifications([speech.env, "discuss.channel/meeting_subtitle"]);
        expect(speech.state.activeSubtitles).toEqual([], { message: "not watching: ignored" });
        speech.state.subtitlesEnabled = true;
        send("discuss.channel/meeting_subtitle", { ...caption, channel_id: channelId + 1, text: "Elsewhere." });
        send("discuss.channel/meeting_subtitle", { ...caption, text: "Shown." });
        await waitUntil(() => speech.state.activeSubtitles.length);
        expect(speech.state.activeSubtitles.map((s) => s.text)).toEqual(["Shown."]);
        expect(speech.state.activeSubtitles[0].speaker).toBe("Bob");
    });

    test("the call's state follows the server", async () => {
        const speech = await startSpeech();
        fakeCapture(speech);
        speech.state.activeChannelId = channelId;
        send("discuss.channel/meeting_ai_state", { channel_id: channelId + 1, transcribe: true, subtitles: true });
        send("discuss.channel/meeting_ai_state", { channel_id: channelId, transcribe: false, subtitles: true });
        await waitUntil(() => speech.state.subtitlesActive);
        expect(speech.state.transcribeEnabled).toBe(false, { message: "another call's state is ignored" });
        expect.verifySteps(["capture started"]);
    });
});

describe("call state", () => {
    test("joining a call picks up what it has on", async () => {
        onRpc("/discuss/meeting/state", ({ url }) => {
            expect.step("state");
            return { channel_id: channelId, transcribe: true, subtitles: false };
        });
        const speech = await startSpeech();
        fakeCapture(speech);
        await speech.joinedCall({ id: channelId });
        expect(speech.state.activeChannelId).toBe(channelId);
        expect(speech.state.transcribeEnabled).toBe(true);
        await expect.waitForSteps([
            "state",
            "This call is being transcribed: everyone's speech is recorded for the meeting summary.",
            "capture started",
        ]);
        // already known: not announced again
        speech.applyAiState({ channel_id: channelId, transcribe: true, subtitles: true });
        expect(speech.state.subtitlesActive).toBe(true);
        expect.verifySteps([]);
        speech.applyAiState({ channel_id: channelId, transcribe: false, subtitles: false });
        expect.verifySteps(["capture stopped"]);
    });

    test("state of another call or an error is ignored", async () => {
        const speech = await startSpeech();
        fakeCapture(speech);
        speech.state.activeChannelId = channelId;
        speech.applyAiState({ channel_id: channelId + 1, transcribe: true });
        speech.applyAiState({ channel_id: channelId, error: "not_in_call", transcribe: true });
        speech.applyAiState(null);
        expect(speech.state.transcribeEnabled).toBe(false);
        expect.verifySteps([]);
    });

    test("a microphone that failed is not asked for again in this call", async () => {
        const speech = await startSpeech();
        fakeCapture(speech);
        speech.state.activeChannelId = channelId;
        speech.micUnavailable = true;
        speech.applyAiState({ channel_id: channelId, subtitles: true });
        expect.verifySteps([]);
    });

    test("a failed state request leaves the call as it is", async () => {
        onRpc("/discuss/meeting/state", () => {
            throw new Error("offline");
        });
        const speech = await startSpeech();
        await speech.joinedCall({ id: channelId });
        expect(speech.state.activeChannelId).toBe(channelId);
        await speech.joinedCall(null); // nothing to join
        expect(speech.state.activeChannelId).toBe(channelId);
    });

    test("leaving resets the meeting", async () => {
        const speech = await startSpeech();
        Object.assign(speech.state, {
            activeChannelId: channelId,
            transcribeEnabled: true,
            subtitlesEnabled: true,
            meetingStartTime: Date.now(),
        });
        speech.lockedLanguage = "fr";
        speech.micUnavailable = true;
        speech.pending = [{ samples: new Float32Array(10), channelId }];
        speech.resetMeeting();
        expect(speech.state.activeChannelId).toBe(null);
        expect(speech.state.transcribeEnabled).toBe(false);
        expect(speech.state.subtitlesEnabled).toBe(false);
        expect(speech.lockedLanguage).toBe(null);
        expect(speech.micUnavailable).toBe(false);
        expect(speech.pending).toEqual([]);
    });

    test("meeting duration", async () => {
        const speech = await startSpeech();
        expect(speech.getDurationMinutes()).toBe(1);
        speech.state.meetingStartTime = Date.now() - 125000;
        expect(speech.getDurationMinutes()).toBe(2);
    });
});

describe("toggles", () => {
    test("Subtitle(CC) on and off", async () => {
        onRpc("/discuss/meeting/state", () => ({ channel_id: channelId, transcribe: false, subtitles: false }));
        onRpc("/discuss/meeting/set_subtitles", async (request) => {
            const { params } = await request.json();
            expect.step(`subtitles ${params.enabled}`);
            return { channel_id: channelId, transcribe: false, subtitles: params.enabled };
        });
        const speech = await startSpeech();
        fakeCapture(speech);
        await speech.toggleSubtitles({ id: channelId });
        expect(speech.state.subtitlesEnabled).toBe(true);
        expect.verifySteps(["subtitles true", "capture started"]);
        speech.updateActiveSubtitle({ id: "x", speaker: "Bob", text: "Hello" });
        await speech.toggleSubtitles({ id: channelId });
        expect(speech.state.subtitlesEnabled).toBe(false);
        expect(speech.state.activeSubtitles).toEqual([], { message: "no captions left on screen" });
        expect.verifySteps(["subtitles false", "capture stopped"]);
    });

    test("Transcribe on and off", async () => {
        onRpc("/discuss/meeting/state", () => ({ channel_id: channelId, transcribe: false, subtitles: false }));
        onRpc("/discuss/meeting/set_transcribe", async (request) => {
            const { params } = await request.json();
            return { channel_id: channelId, transcribe: params.enabled, subtitles: false };
        });
        const speech = await startSpeech();
        fakeCapture(speech);
        await speech.toggleTranscribe({ id: channelId });
        expect(speech.state.transcribeEnabled).toBe(true);
        expect.verifySteps([
            "This call is being transcribed: everyone's speech is recorded for the meeting summary.",
            "capture started",
        ]);
        await speech.toggleTranscribe({ id: channelId });
        expect(speech.state.transcribeEnabled).toBe(false);
        expect.verifySteps(["capture stopped", "Transcription stopped."]);
    });

    test("Transcribe refused by the server changes nothing", async () => {
        onRpc("/discuss/meeting/state", () => ({ channel_id: channelId, transcribe: false, subtitles: false }));
        onRpc("/discuss/meeting/set_transcribe", () => ({ error: "not_allowed" }));
        const speech = await startSpeech();
        fakeCapture(speech);
        await speech.toggleTranscribe({ id: channelId });
        expect(speech.state.transcribeEnabled).toBe(false);
        expect.verifySteps([]);
    });

    test("a browser without audio capture", async () => {
        onRpc("/discuss/meeting/set_subtitles", () => expect.step("set_subtitles"));
        const speech = await startSpeech();
        speech.state.isSupported = false;
        await speech.toggleSubtitles({ id: channelId });
        await speech.toggleTranscribe({ id: channelId });
        await speech.toggleSubtitles(null);
        expect.verifySteps([
            "Microphone audio recording is not supported in this browser.",
            "Microphone audio recording is not supported in this browser.",
        ]);
        expect(speech.state.subtitlesEnabled).toBe(false);
    });
});

describe("cutting speech into utterances", () => {
    /** A listening service whose finished utterances are recorded instead of sent. */
    async function listening() {
        const speech = await startSpeech();
        const utterances = [];
        patchWithCleanup(speech, {
            queueUtterance(chunks, sampleRate) {
                utterances.push(this.toSamples(chunks, sampleRate));
            },
        });
        speech.state.isListening = true;
        speech.resetSegmenter();
        const feed = (...blocks) => blocks.forEach((b) => speech.onAudioBlock(b, RATE));
        return { speech, utterances, feed };
    }

    const times = (n, make) => Array.from({ length: n }, make);

    test("an utterance ends after half a second of silence", async () => {
        const { utterances, feed } = await listening();
        feed(...times(5, silence), ...times(10, voice), ...times(3, silence));
        expect(utterances).toHaveLength(0, { message: "0.38 s of silence: still talking" });
        feed(silence());
        expect(utterances).toHaveLength(1);
        // 2 blocks of the silence before (first syllables), 10 of voice, 4 of trailing silence
        expect(utterances[0]).toHaveLength(16 * BLOCK);
    });

    test("clicks and coughs are not utterances", async () => {
        const { utterances, feed } = await listening();
        feed(...times(2, voice), ...times(4, silence)); // a cough: started, but too short
        feed(voice(), ...times(5, silence)); // a click: never starts an utterance
        expect(utterances).toHaveLength(0);
    });

    test("long speech is cut at the quietest moment", async () => {
        const { speech, utterances, feed } = await listening();
        feed(...times(40, voice), silence(), ...times(5, voice));
        expect(utterances).toHaveLength(0);
        feed(voice()); // 6 s reached
        expect(utterances).toHaveLength(1);
        // the cut falls in the gap between words, not in the middle of one
        expect(utterances[0].length).toBeGreaterThan(40 * BLOCK);
        expect(utterances[0].length).toBeLessThan(41 * BLOCK);
        const carried = speech.segmenter.chunks[0].length;
        expect(utterances[0].length + carried).toBe(47 * BLOCK, { message: "the rest is carried over" });
    });

    test("background noise raises the bar for speech", async () => {
        const { speech, utterances, feed } = await listening();
        feed(...times(200, () => voice(0.011))); // a steady hum just under the minimum level
        expect(speech.segmenter.noiseFloor).toBeGreaterThan(0.01);
        feed(...times(10, () => voice(0.015)), ...times(5, () => voice(0.011)));
        expect(utterances).toHaveLength(0, { message: "barely above the hum: not speech" });
        feed(...times(10, () => voice(0.1)), ...times(5, () => voice(0.011)));
        expect(utterances).toHaveLength(1);
    });

    test("nothing is captured while muted or not listening", async () => {
        const { speech, utterances, feed } = await listening();
        feed(...times(10, voice));
        expect(speech.segmenter.speaking).toBe(true);
        patchWithCleanup(speech, { isMuted: () => true });
        feed(...times(5, silence));
        expect(speech.segmenter.speaking).toBe(false, { message: "what was being said is dropped" });
        expect(speech.segmenter.chunks).toEqual([]);
        speech.state.isListening = false;
        feed(...times(10, voice));
        expect(utterances).toHaveLength(0);
    });

    test("audio from the browser at 48 kHz is brought down to 16 kHz", async () => {
        const speech = await startSpeech();
        const block = new Float32Array(4800);
        for (let i = 0; i < block.length; i++) {
            block[i] = [0, 0.3, 0.6][i % 3];
        }
        const samples = speech.toSamples([block, block], 48000);
        expect(samples).toHaveLength(3200);
        expect(Math.abs(samples[0] - 0.3)).toBeLessThan(1e-6);
        expect(speech.toSamples([block], RATE)).toHaveLength(4800, { message: "already 16 kHz" });
    });
});

describe("sending utterances", () => {
    /** Sends recorded instead of posted, each finished when the test says so. */
    async function sending() {
        const speech = await startSpeech();
        const sent = [];
        patchWithCleanup(speech, {
            sendUtterance(wav, channel) {
                let done;
                sent.push({ wav, channel, promise: new Promise((resolve) => (done = resolve)) });
                sent.at(-1).done = done;
                return sent.at(-1).promise;
            },
        });
        speech.state.activeChannelId = channelId;
        return { speech, sent };
    }

    const seconds = (s) => new Float32Array(Math.round(s * RATE)).fill(0.5);

    test("one request at a time: what piles up meanwhile goes together", async () => {
        const { speech, sent } = await sending();
        speech.pending.push({ samples: seconds(1), channelId });
        speech.flushPending();
        speech.pending.push({ samples: seconds(2), channelId }, { samples: seconds(3), channelId });
        speech.flushPending();
        expect(sent).toHaveLength(1);
        expect(sent[0].wav.size).toBe(44 + 2 * RATE);
        sent[0].done();
        await waitUntil(() => sent.length === 2);
        // 2 s and 3 s, with 0.2 s of silence between them
        expect(sent[1].wav.size).toBe(44 + 2 * (5 * RATE + 0.2 * RATE));
        expect(sent[1].channel).toBe(channelId);
    });

    test("a backlog too long for Whisper drops the oldest speech", async () => {
        const { speech, sent } = await sending();
        speech.sending = true; // a request in flight
        speech.pending.push(...[12, 12, 12].map((s) => ({ samples: seconds(s), channelId })));
        speech.sending = false;
        speech.flushPending();
        expect(sent[0].wav.size).toBe(44 + 2 * (24 * RATE + 0.2 * RATE));
    });

    test("utterances of different calls are not sent together", async () => {
        const { speech, sent } = await sending();
        speech.pending.push({ samples: seconds(1), channelId }, { samples: seconds(1), channelId: 999 });
        speech.flushPending();
        expect(sent).toHaveLength(1);
        sent[0].done();
        await waitUntil(() => sent.length === 2);
        expect(sent[1].channel).toBe(999);
    });

    test("a WAV file Whisper can read", async () => {
        const { speech, sent } = await sending();
        speech.queueUtterance([new Float32Array([0.5, -1, 2])], RATE);
        // read natively: Hoot's mock Blob can't give back the DataView the WAV is built from
        const buffer = await new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.readAsArrayBuffer(sent[0].wav);
        });
        const view = new DataView(buffer);
        const text = (offset) => String.fromCharCode(...new Uint8Array(view.buffer, offset, 4));
        expect([text(0), text(8), text(12), text(36)]).toEqual(["RIFF", "WAVE", "fmt ", "data"]);
        expect(view.getUint16(22, true)).toBe(1, { message: "mono" });
        expect(view.getUint32(24, true)).toBe(RATE);
        expect(view.getUint16(34, true)).toBe(16, { message: "16-bit" });
        expect(view.getUint32(40, true)).toBe(6);
        expect(view.getInt16(44, true)).toBe(16383);
        expect(view.getInt16(46, true)).toBe(-32768);
        expect(view.getInt16(48, true)).toBe(32767, { message: "clipped" });
        expect(sent[0].wav.type).toBe("audio/wav");
    });
});

describe("transcription replies", () => {
    const wav = () => new Blob(["RIFF"], { type: "audio/wav" });

    /** Replies of the transcription route, in order; each request's language is a step. */
    function transcribeReplies(...replies) {
        onRpc("/discuss/meeting/transcribe_chunk", async (request) => {
            const form = await request.formData();
            expect.step(form.get("language") || "detect");
            expect(form.get("channel_id")).toBe(String(channelId));
            expect(form.get("file").name).toBe("audio.wav");
            const reply = typeof replies[0] === "function" ? replies[0]() : replies[0];
            if (replies.length > 1) {
                replies.shift();
            }
            return reply;
        });
    }

    test("the speaker's language is locked once two captions agree, then checked again now and then", async () => {
        transcribeReplies({ text: "Bonjour", language: "fr", language_probability: 0.5 });
        const speech = await startSpeech();
        speech.state.activeChannelId = channelId;
        for (let i = 0; i < 8; i++) {
            await speech.sendUtterance(wav(), channelId);
        }
        expect.verifySteps(["detect", "detect", "fr", "fr", "fr", "fr", "fr", "detect"]);
        expect(speech.lockedLanguage).toBe("fr");
    });

    test("a confident detection locks at once; a caption without words changes nothing", async () => {
        transcribeReplies(
            { text: "", language: "de", language_probability: 1 },
            { text: "Wir fangen jetzt an.", language: "de", language_probability: 0.95 },
            { text: "Gut.", language: "de", language_probability: 0.95 }
        );
        const speech = await startSpeech();
        speech.state.activeChannelId = channelId;
        await speech.sendUtterance(wav(), channelId);
        expect(speech.lockedLanguage).toBe(null);
        await speech.sendUtterance(wav(), channelId);
        expect(speech.lockedLanguage).toBe("de");
        await speech.sendUtterance(wav(), channelId);
        expect.verifySteps(["detect", "detect", "de"]);
    });

    test("a re-check that disagrees detects again until two captions agree", async () => {
        const speech = await startSpeech();
        speech.lockedLanguage = "en";
        speech.lockedCaptions = 5;
        speech.languageStreak = { language: "en", count: 2 };
        speech.updateLanguage({ text: "Hola a todos", language: "es", language_probability: 0.5 }, true);
        expect(speech.lockedLanguage).toBe("en");
        speech.updateLanguage({ text: "Seguimos", language: "es", language_probability: 0.5 }, true);
        expect(speech.lockedLanguage).toBe("es");
        speech.updateLanguage({ text: "x", language: null }, true);
        expect(speech.lockedLanguage).toBe("es");
    });

    test("own caption shown while watching subtitles, with the call's state", async () => {
        transcribeReplies({ text: "Ship it today.", language: "en", language_probability: 1,
                            transcribe: true, subtitles: true });
        const speech = await startSpeech();
        fakeCapture(speech);
        speech.state.activeChannelId = channelId;
        speech.state.subtitlesEnabled = true;
        await speech.sendUtterance(wav(), channelId);
        expect.verifySteps([
            "detect",
            "This call is being transcribed: everyone's speech is recorded for the meeting summary.",
            "capture started",
        ]);
        expect(speech.state.transcribeEnabled).toBe(true);
        const [caption] = speech.state.activeSubtitles;
        expect(caption.text).toBe("Ship it today.");
        expect(caption.speaker).toBe(speech.store.self_partner.name);
        expect(caption.id).toMatch(/^local-user-/);
    });

    test("nothing shown when not watching, or when the call moved on", async () => {
        transcribeReplies({ text: "Ship it today.", language: "en", language_probability: 1 });
        const speech = await startSpeech();
        speech.state.activeChannelId = channelId;
        await speech.sendUtterance(wav(), channelId);
        expect(speech.state.activeSubtitles).toEqual([]);
        expect(speech.lockedLanguage).toBe("en", { message: "the language is learned all the same" });
        speech.lockedLanguage = null;
        speech.state.subtitlesEnabled = true;
        speech.state.activeChannelId = channelId + 1;
        await speech.sendUtterance(wav(), channelId);
        await speech.sendUtterance(wav(), null); // no call: nothing sent
        expect(speech.state.activeSubtitles).toEqual([]);
        expect(speech.lockedLanguage).toBe(null, { message: "a reply for an old call teaches nothing" });
        expect.verifySteps(["detect", "detect"]);
    });

    test("why a caption was lost is told, but not for every caption", async () => {
        transcribeReplies({ text: "", caption_error: "Captions skipped: xAI has reached its limit." });
        const speech = await startSpeech();
        speech.state.activeChannelId = channelId;
        await speech.sendUtterance(wav(), channelId);
        await speech.sendUtterance(wav(), channelId);
        expect.verifySteps(["detect", "Captions skipped: xAI has reached its limit.", "detect"]);
        speech.captionErrorShownAt["Captions skipped: xAI has reached its limit."] -= 31000;
        await speech.sendUtterance(wav(), channelId);
        expect.verifySteps(["detect", "Captions skipped: xAI has reached its limit."]);
    });

    test("a failed request loses only this caption", async () => {
        onRpc("/discuss/meeting/transcribe_chunk", () => {
            throw new Error("server down");
        });
        const speech = await startSpeech();
        speech.state.activeChannelId = channelId;
        await speech.sendUtterance(wav(), channelId);
        expect(speech.state.activeSubtitles).toEqual([]);
    });
});

describe("microphone", () => {
    function fakeStream() {
        return { getTracks: () => [{ stop: () => expect.step("track stopped") }] };
    }

    test("denied: the speaker is told once, and not asked again", async () => {
        const speech = await startSpeech();
        if (!speech.state.isSupported) {
            return; // no audio capture in this browser: nothing to start
        }
        patchWithCleanup(navigator.mediaDevices, {
            getUserMedia: () => Promise.reject(new DOMException("denied", "NotAllowedError")),
        });
        patchWithCleanup(console, { warn: () => expect.step("warned") });
        Object.assign(speech.state, { activeChannelId: channelId, transcribeEnabled: true });
        await speech.startAudioCapture();
        expect.verifySteps([
            "warned",
            "Could not access the microphone: your speech cannot be captioned or transcribed.",
        ]);
        expect(speech.micUnavailable).toBe(true);
        expect(speech.state.isStreamingAudio).toBe(false);
        speech.syncCapture();
        expect.verifySteps([]);
    });

    test("no longer needed once the permission prompt was answered", async () => {
        const speech = await startSpeech();
        if (!speech.state.isSupported) {
            return;
        }
        patchWithCleanup(navigator.mediaDevices, { getUserMedia: async () => fakeStream() });
        speech.state.activeChannelId = channelId; // neither transcription nor subtitles on
        await speech.startAudioCapture();
        expect.verifySteps(["track stopped"]);
        expect(speech.state.isStreamingAudio).toBe(false);
    });

    test("stopped while the browser was still asking", async () => {
        const speech = await startSpeech();
        if (!speech.state.isSupported) {
            return;
        }
        let grant;
        patchWithCleanup(navigator.mediaDevices, {
            getUserMedia: () => new Promise((resolve) => (grant = resolve)),
        });
        Object.assign(speech.state, { activeChannelId: channelId, transcribeEnabled: true });
        const starting = speech.startAudioCapture();
        speech.startAudioCapture(); // already starting: no second prompt
        speech.stopCapture();
        grant(fakeStream());
        await starting;
        expect.verifySteps(["track stopped"]);
        expect(speech.stream).toBe(null);
    });

    test("stopping releases everything", async () => {
        const speech = await startSpeech();
        const node = (name) => ({
            port: {},
            disconnect: () => expect.step(`${name} disconnected`),
        });
        Object.assign(speech, {
            captureNode: node("capture"),
            sourceNode: node("source"),
            filterNode: node("filter"),
            audioContext: { close: async () => expect.step("context closed") },
            stream: fakeStream(),
            pending: [{ samples: new Float32Array(1), channelId }],
        });
        speech.state.isListening = true;
        speech.stopCapture();
        expect.verifySteps([
            "capture disconnected",
            "source disconnected",
            "filter disconnected",
            "context closed",
            "track stopped",
        ]);
        expect(speech.state.isListening).toBe(false);
        expect(speech.pending).toEqual([]);
        expect(speech.segmenter).toBe(null);
    });
});
