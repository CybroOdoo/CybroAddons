/** @odoo-module **/

import { reactive } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

const AudioContextClass =
    typeof window !== "undefined" && (window.AudioContext || window.webkitAudioContext);
const CanCaptureAudio = Boolean(
    AudioContextClass &&
        typeof AudioWorkletNode !== "undefined" &&
        navigator.mediaDevices?.getUserMedia
);

// Audio pipeline tuning (all times in seconds)
const TARGET_SAMPLE_RATE = 16000; // what Whisper expects
const MIN_RMS_THRESHOLD = 0.012; // never treat anything quieter than this as speech
const NOISE_MARGIN = 2; // speech must be this many times louder than the noise floor
const END_SILENCE = 0.5; // silence that closes an utterance
const MAX_UTTERANCE = 6; // force a cut so captions keep flowing
const MIN_UTTERANCE = 0.4; // ignore clicks and coughs
const PRE_ROLL = 0.3; // audio kept before speech onset so first syllables aren't clipped
const MIN_ONSET = 0.2; // voice must last this long to start an utterance (a single click doesn't)
const SPLIT_SEARCH = 2; // a forced cut happens at the quietest point of this last stretch
const SPLIT_WINDOW = 0.03; // ...found by comparing windows this long (a gap between words lasts a few of them)
const SPLIT_STEP = 0.01; // ...every this often
const MAX_BATCH = 28; // Whisper hears at most 30 s at once: older backlog beyond this is dropped
const BATCH_GAP = 0.2; // silence inserted between utterances sent together
const LANGUAGE_LOCK_PROBABILITY = 0.9; // auto-detected language reused once this confident
const LANGUAGE_LOCK_MIN_CHARS = 12; // ...on a caption at least this long
const LANGUAGE_STREAK = 2; // ...or once this many captions in a row came out in the same language
const LANGUAGE_RECHECK = 5; // a locked language is detected again every this many captions
const CAPTION_HOLD = 6; // each caption stays on screen this long, so it can be read
const MAX_CAPTION_LINES = 3; // caption lines shown at once: the oldest go first beyond this
const CAPTION_ERROR_INTERVAL = 30; // the same caption failure is shown at most this often
// Hum and rumble (fans, air conditioning, a knocked desk) lie below this, voices above: removing
// them keeps that noise from passing for speech. Hz.
const HIGH_PASS_FREQUENCY = 100;
const HIGH_PASS_Q = -3.01; // in dB for a high-pass filter: a flat (Butterworth) response

// Runs in the audio thread: forwards mic samples to the main thread in blocks.
const CAPTURE_WORKLET = `
class MeetingCaptureProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.buffer = new Float32Array(2048);
        this.length = 0;
    }
    process(inputs) {
        const channel = inputs[0] && inputs[0][0];
        if (channel) {
            for (let i = 0; i < channel.length; i++) {
                this.buffer[this.length++] = channel[i];
                if (this.length === this.buffer.length) {
                    this.port.postMessage(this.buffer.slice(0));
                    this.length = 0;
                }
            }
        }
        return true;
    }
}
registerProcessor("meeting-capture", MeetingCaptureProcessor);
`;

/** Concatenate Float32Array blocks. */
function concatBlocks(blocks) {
    const merged = new Float32Array(blocks.reduce((n, b) => n + b.length, 0));
    let offset = 0;
    for (const b of blocks) {
        merged.set(b, offset);
        offset += b.length;
    }
    return merged;
}

/**
 * Index of the quietest moment in the last ``seconds`` of ``samples``: the middle of the
 * lowest-energy window, most likely a gap between two words. Mic blocks (~130 ms) are too
 * coarse for that in fluent speech, where those gaps are often shorter.
 */
function quietestPoint(samples, sampleRate, seconds) {
    const win = Math.max(1, Math.round(SPLIT_WINDOW * sampleRate));
    const step = Math.max(1, Math.round(SPLIT_STEP * sampleRate));
    const start = Math.max(0, samples.length - Math.round(seconds * sampleRate));
    let best = samples.length - Math.floor(win / 2);
    let bestEnergy = Infinity;
    for (let i = start; i + win <= samples.length; i += step) {
        let energy = 0;
        for (let j = i; j < i + win; j++) {
            energy += samples[j] * samples[j];
        }
        if (energy < bestEnergy) {
            bestEnergy = energy;
            best = i + Math.floor(win / 2);
        }
    }
    return best;
}

function downsample(samples, fromRate, toRate) {
    if (fromRate === toRate) {
        return samples;
    }
    const ratio = fromRate / toRate;
    const out = new Float32Array(Math.floor(samples.length / ratio));
    for (let i = 0; i < out.length; i++) {
        // average the source window to act as a cheap low-pass filter
        const start = Math.floor(i * ratio);
        const end = Math.min(samples.length, Math.floor((i + 1) * ratio));
        let sum = 0;
        for (let j = start; j < end; j++) {
            sum += samples[j];
        }
        out[i] = sum / Math.max(1, end - start);
    }
    return out;
}

function encodeWav(samples, sampleRate) {
    const view = new DataView(new ArrayBuffer(44 + samples.length * 2));
    const writeStr = (offset, str) => {
        for (let i = 0; i < str.length; i++) {
            view.setUint8(offset + i, str.charCodeAt(i));
        }
    };
    writeStr(0, "RIFF");
    view.setUint32(4, 36 + samples.length * 2, true);
    writeStr(8, "WAVE");
    writeStr(12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM
    view.setUint16(22, 1, true); // mono
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeStr(36, "data");
    view.setUint32(40, samples.length * 2, true);
    for (let i = 0; i < samples.length; i++) {
        const v = Math.max(-1, Math.min(1, samples[i]));
        view.setInt16(44 + i * 2, v < 0 ? v * 0x8000 : v * 0x7fff, true);
    }
    return new Blob([view], { type: "audio/wav" });
}

export class MeetingSpeechService {
    constructor(env, services) {
        this.env = env;
        this.busService = services.bus_service;
        this.notification = services.notification;
        this.store = services["mail.store"];

        this.state = reactive({
            isSupported: CanCaptureAudio,
            subtitlesEnabled: false, // this participant watches Subtitle(CC)
            // Call-wide, from the server: the call is transcribed into its meeting summary /
            // at least one participant watches subtitles. Either one makes everyone's mic captured.
            transcribeEnabled: false,
            subtitlesActive: false,
            isListening: false,
            activeSubtitles: [], // [{ id, speaker, text, time, expiresAt }]
            meetingStartTime: null,
            activeChannelId: null,
            isStreamingAudio: false,
        });

        this.audioContext = null;
        this.captureNode = null;
        this.sourceNode = null;
        this.stream = null;
        this.captureAttempt = 0; // bumped by each start and stop: a start that awaited past a newer one gives up
        this.pending = []; // [{ samples, channelId }] at 16 kHz, waiting while a request is in flight
        this.sending = false;
        this.lockedLanguage = null; // language detected for this speaker when set to auto-detect
        this.languageStreak = { language: null, count: 0 };
        this.lockedCaptions = 0; // captions since the locked language was last checked
        this.fadeTimeout = null;
        this.captionCount = 0; // gives each caption line its own id
        this.captionErrorShownAt = {}; // failure message -> when it was last shown
        this.micUnavailable = false; // denied or failed in this call: don't prompt again on every change
        this.initBus();
    }

    initBus() {
        if (!this.busService) {
            return;
        }
        this.busService.subscribe("discuss.channel/meeting_subtitle", (payload) => {
            if (!this.state.subtitlesEnabled || payload.channel_id !== this.state.activeChannelId) {
                return;
            }
            this.handleIncomingSubtitle(payload);
        });
        this.busService.subscribe("discuss.channel/meeting_ai_state", (payload) => {
            if (payload.channel_id === this.state.activeChannelId) {
                this.applyAiState(payload);
            }
        });
    }

    /** Called once this participant is in the call of ``channel``: pick up the call's state. */
    async joinedCall(channel) {
        if (!channel) {
            return;
        }
        if (this.state.activeChannelId !== channel.id) {
            this.resetMeeting();
            this.state.activeChannelId = channel.id;
            this.state.meetingStartTime = Date.now();
        }
        try {
            this.applyAiState(await rpc("/discuss/meeting/state", { channel_id: channel.id }));
        } catch {
            // the bus sends the call's state as soon as it changes
        }
    }

    applyAiState(aiState) {
        if (!aiState || aiState.error || aiState.channel_id !== this.state.activeChannelId) {
            return;
        }
        const transcribe = Boolean(aiState.transcribe);
        if (transcribe && !this.state.transcribeEnabled) {
            // everyone in the call, whoever turned it on (or on joining a call already transcribed)
            this.notification?.add(
                _t(
                    "This call is being transcribed: everyone's speech is recorded for the meeting summary."
                ),
                { type: "info" }
            );
        }
        this.state.transcribeEnabled = transcribe;
        this.state.subtitlesActive = Boolean(aiState.subtitles);
        this.syncCapture();
    }

    /** Capture this participant's microphone exactly while the call needs it. */
    syncCapture() {
        const needed = Boolean(
            this.state.activeChannelId &&
                (this.state.transcribeEnabled || this.state.subtitlesActive)
        );
        if (needed && !this.state.isStreamingAudio && !this.micUnavailable) {
            this.startAudioCapture();
        } else if (!needed && this.state.isStreamingAudio) {
            this.stopCapture();
        }
    }

    handleIncomingSubtitle({ partner_id, member_id, partner_name, text, time }) {
        const store = this.store || this.env?.services?.["mail.store"];
        // Our own captions are already shown locally. Compare channel members, not partners:
        // every guest shares the public partner.
        const selfMemberId = store?.rtc?.selfSession?.channel_member_id?.id;
        const isSelf = member_id
            ? member_id === selfMemberId
            : Boolean(store?.self_partner && partner_id === store.self_partner.id);
        // the member tells guests apart: they all share the public partner
        const id = member_id ? `remote-member-${member_id}` : `remote-${partner_id || "guest"}`;

        // If it's from another participant, display it in activeSubtitles
        if (!isSelf) {
            this.updateActiveSubtitle({
                id,
                speaker: partner_name,
                text,
                time:
                    time ||
                    new Date().toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                    }),
            });
        }
    }

    /**
     * Show a caption of the speaker ``id``. Each caption gets its own line, below the earlier
     * ones, and stays CAPTION_HOLD seconds even when the next one follows right away, so it can
     * be read.
     */
    updateActiveSubtitle({ id, speaker, text, time }) {
        const item = {
            id: `${id}-${++this.captionCount}`,
            speaker: speaker || _t("Speaker"),
            text,
            time:
                time ||
                new Date().toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                }),
            expiresAt: Date.now() + CAPTION_HOLD * 1000,
        };
        // the oldest lines make room when people keep talking
        this.state.activeSubtitles = [...this.state.activeSubtitles, item].slice(-MAX_CAPTION_LINES);
        this.scheduleCaptionExpiry();
    }

    /** Remove each caption line once its time is up. */
    scheduleCaptionExpiry() {
        clearTimeout(this.fadeTimeout);
        if (!this.state.activeSubtitles.length) {
            return;
        }
        const next = Math.min(...this.state.activeSubtitles.map((s) => s.expiresAt));
        this.fadeTimeout = setTimeout(() => {
            const now = Date.now();
            this.state.activeSubtitles = this.state.activeSubtitles.filter((s) => s.expiresAt > now);
            this.scheduleCaptionExpiry();
        }, Math.max(0, next - Date.now()) + 50);
    }

    checkSupported() {
        if (!this.state.isSupported) {
            this.notification?.add(
                _t("Microphone audio recording is not supported in this browser."),
                { type: "warning" }
            );
        }
        return this.state.isSupported;
    }

    /** Subtitle(CC): show captions to this participant; everyone is captioned meanwhile. */
    async toggleSubtitles(channel) {
        if (!channel || !this.checkSupported()) {
            return;
        }
        if (this.state.activeChannelId !== channel.id) {
            await this.joinedCall(channel);
        }
        const enabled = !this.state.subtitlesEnabled;
        this.state.subtitlesEnabled = enabled;
        if (!enabled) {
            this.state.activeSubtitles = [];
        }
        this.applyAiState(
            await rpc("/discuss/meeting/set_subtitles", { channel_id: channel.id, enabled })
        );
    }

    /** Transcribe: record everyone's speech into the meeting summary, for the whole call. */
    async toggleTranscribe(channel) {
        if (!channel || !this.checkSupported()) {
            return;
        }
        if (this.state.activeChannelId !== channel.id) {
            await this.joinedCall(channel);
        }
        const enabled = !this.state.transcribeEnabled;
        const result = await rpc("/discuss/meeting/set_transcribe", {
            channel_id: channel.id,
            enabled,
        });
        if (result?.error) {
            return; // not in the call, or not allowed to change it: nothing changed
        }
        this.applyAiState(result);
        if (!enabled) {
            // starting is announced to everyone by applyAiState
            this.notification?.add(_t("Transcription stopped."), { type: "info" });
        }
    }

    async startAudioCapture() {
        if (this.state.isStreamingAudio || !CanCaptureAudio) {
            return;
        }
        this.state.isStreamingAudio = true;
        const attempt = ++this.captureAttempt;
        // stopped (or stopped and started again) while this start awaited the browser
        const superseded = () => attempt !== this.captureAttempt;
        let stream = null;
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    echoCancellation: true,
                    // Browser denoising distorts speech more than Whisper's own robustness to noise
                    noiseSuppression: false,
                    autoGainControl: true,
                },
            });
            if (superseded()) {
                stream.getTracks().forEach((t) => t.stop());
                return;
            }
            if (!this.state.transcribeEnabled && !this.state.subtitlesActive) {
                // no longer needed once the permission prompt was answered
                stream.getTracks().forEach((t) => t.stop());
                this.state.isStreamingAudio = false;
                return;
            }
            this.stream = stream;

            // Ask the browser to resample to 16 kHz itself (much better than our fallback).
            // Firefox refuses to connect a mic stream to a different-rate context, so fall back.
            let context = new AudioContextClass({ sampleRate: TARGET_SAMPLE_RATE });
            try {
                context.createMediaStreamSource(stream);
            } catch {
                context.close().catch(() => {});
                context = new AudioContextClass();
            }
            this.audioContext = context;
            const workletUrl = URL.createObjectURL(
                new Blob([CAPTURE_WORKLET], { type: "application/javascript" })
            );
            try {
                await context.audioWorklet.addModule(workletUrl);
            } finally {
                URL.revokeObjectURL(workletUrl);
            }
            if (superseded()) {
                return; // the stop already closed this context and stream
            }
            this.sourceNode = context.createMediaStreamSource(stream);
            this.filterNode = context.createBiquadFilter();
            this.filterNode.type = "highpass";
            this.filterNode.frequency.value = HIGH_PASS_FREQUENCY;
            this.filterNode.Q.value = HIGH_PASS_Q;
            this.captureNode = new AudioWorkletNode(context, "meeting-capture");
            // Not connected to the destination: we only listen, never play back.
            this.sourceNode.connect(this.filterNode).connect(this.captureNode);

            this.resetSegmenter();
            this.captureNode.port.onmessage = (e) => this.onAudioBlock(e.data, context.sampleRate);
            this.state.isListening = true;
        } catch (err) {
            if (superseded()) {
                // failed because it was stopped meanwhile (closed context), not for want of a microphone
                stream?.getTracks().forEach((t) => t.stop());
                return;
            }
            console.warn("Could not start audio capture:", err);
            this.micUnavailable = true;
            this.notification?.add(
                _t(
                    "Could not access the microphone: your speech cannot be captioned or transcribed."
                ),
                { type: "warning" }
            );
            this.stopCapture();
        }
    }

    resetSegmenter() {
        this.segmenter = {
            preRoll: [], // blocks kept while idle
            preRollSeconds: 0,
            onset: 0, // consecutive voice while idle, in seconds
            chunks: [], // blocks of the current utterance
            seconds: 0,
            silence: 0,
            speaking: false,
            noiseFloor: this.segmenter?.noiseFloor ?? MIN_RMS_THRESHOLD / NOISE_MARGIN,
        };
    }

    /** Whether the user muted themselves in the call: nothing they say may then be captioned. */
    isMuted() {
        const store = this.store || this.env?.services?.["mail.store"];
        return Boolean(store?.rtc?.selfSession?.isMute);
    }

    /** Energy-based voice activity detection that cuts the mic stream into utterances. */
    onAudioBlock(block, sampleRate) {
        const seg = this.segmenter;
        if (!seg || !this.state.isListening) {
            return;
        }
        if (this.isMuted()) {
            // drop whatever was being said when the user muted, and listen to nothing until unmuted
            if (seg.speaking || seg.preRoll.length) {
                this.resetSegmenter();
            }
            return;
        }
        const duration = block.length / sampleRate;
        let sum = 0;
        for (let i = 0; i < block.length; i++) {
            sum += block[i] * block[i];
        }
        const rms = Math.sqrt(sum / block.length);
        const threshold = Math.max(MIN_RMS_THRESHOLD, seg.noiseFloor * NOISE_MARGIN);
        const isVoice = rms > threshold;

        if (!seg.speaking) {
            seg.preRoll.push({ block, rms });
            seg.preRollSeconds += duration;
            if (!isVoice) {
                // slowly track the background noise level while idle
                seg.noiseFloor = seg.noiseFloor * 0.95 + rms * 0.05;
                seg.onset = 0;
            } else {
                seg.onset += duration;
            }
            if (seg.onset < MIN_ONSET) {
                while (seg.preRollSeconds > PRE_ROLL + seg.onset && seg.preRoll.length > 1) {
                    seg.preRollSeconds -= seg.preRoll.shift().block.length / sampleRate;
                }
                return;
            }
            seg.speaking = true;
            seg.chunks = seg.preRoll.map((p) => p.block);
            seg.seconds = seg.preRollSeconds;
            seg.preRoll = [];
            seg.preRollSeconds = 0;
            seg.onset = 0;
            seg.silence = 0;
        } else {
            seg.chunks.push(block);
            seg.seconds += duration;
            seg.silence = isVoice ? 0 : seg.silence + duration;
        }

        if (seg.silence >= END_SILENCE) {
            const speechSeconds = seg.seconds - seg.silence;
            const chunks = seg.chunks;
            this.resetSegmenter();
            if (speechSeconds >= MIN_UTTERANCE) {
                this.queueUtterance(chunks, sampleRate);
            }
        } else if (seg.seconds >= MAX_UTTERANCE) {
            // Still talking: cut at the quietest moment of the last stretch (most likely a gap
            // between words) and carry the rest over, rather than splitting a word in half.
            const audio = concatBlocks(seg.chunks);
            const at = quietestPoint(audio, sampleRate, SPLIT_SEARCH);
            this.queueUtterance([audio.subarray(0, at)], sampleRate);
            seg.chunks = [audio.slice(at)];
            seg.seconds = seg.chunks[0].length / sampleRate;
            seg.silence = 0;
        }
    }

    toSamples(chunks, sampleRate) {
        return downsample(concatBlocks(chunks), sampleRate, TARGET_SAMPLE_RATE);
    }

    queueUtterance(chunks, sampleRate) {
        this.pending.push({
            samples: this.toSamples(chunks, sampleRate),
            channelId: this.state.activeChannelId,
        });
        this.flushPending();
    }

    /** Post audio for transcription. Resolves to the server reply. */
    async postAudio(wav, channelId, detectLanguage = false) {
        const formData = new FormData();
        formData.append("file", wav, "audio.wav");
        formData.append("channel_id", channelId);
        formData.append("csrf_token", odoo.csrf_token);
        if (this.lockedLanguage && !detectLanguage) {
            formData.append("language", this.lockedLanguage);
        }
        const res = await fetch("/discuss/meeting/transcribe_chunk", {
            method: "POST",
            body: formData,
        });
        return res.json();
    }

    /**
     * Send what is waiting as one request. While a request is in flight new utterances pile up,
     * and are then sent together: when the server falls behind, captions arrive in bigger
     * pieces instead of an ever-growing queue of stale ones. One request at a time also keeps
     * captions in spoken order.
     */
    async flushPending() {
        if (this.sending || !this.pending.length) {
            return;
        }
        const channelId = this.pending[0].channelId;
        const batch = [];
        while (this.pending.length && this.pending[0].channelId === channelId) {
            batch.push(this.pending.shift().samples);
        }
        const gap = Math.round(BATCH_GAP * TARGET_SAMPLE_RATE);
        const length = (parts) =>
            parts.reduce((n, s) => n + s.length, 0) + gap * (parts.length - 1);
        while (batch.length > 1 && length(batch) > MAX_BATCH * TARGET_SAMPLE_RATE) {
            batch.shift(); // too far behind: the oldest speech is no longer worth captioning
        }
        const samples = new Float32Array(length(batch));
        let offset = 0;
        for (const part of batch) {
            samples.set(part, offset);
            offset += part.length + gap;
        }
        this.sending = true;
        try {
            await this.sendUtterance(encodeWav(samples, TARGET_SAMPLE_RATE), channelId);
        } finally {
            this.sending = false;
            this.flushPending();
        }
    }

    async sendUtterance(wav, channelId) {
        if (!channelId) {
            return;
        }
        const store = this.store || this.env?.services?.["mail.store"];
        const myName = store?.self_partner?.name || _t("You");
        try {
            const recheck = Boolean(this.lockedLanguage) && this.lockedCaptions >= LANGUAGE_RECHECK;
            const data = await this.postAudio(wav, channelId, recheck);
            if (channelId !== this.state.activeChannelId) {
                return; // the meeting ended (or moved) while this was being transcribed
            }
            if (data?.text) {
                this.updateLanguage(data, !this.lockedLanguage || recheck);
            }
            if (data && "transcribe" in data) {
                this.applyAiState({ ...data, channel_id: channelId });
            }
            if (data?.caption_error) {
                this.notifyCaptionError(data.caption_error);
            }
            if (data && data.text) {
                if (this.state.subtitlesEnabled) {
                    this.updateActiveSubtitle({
                        id: "local-user",
                        speaker: myName,
                        text: data.text,
                    });
                }
            }
        } catch {
            // network or server error: this caption is lost, the next one is sent normally
        }
    }

    /**
     * Tell the speaker why their caption was lost (the cloud speech engine failed). A failure that
     * repeats, like a rate limit, is shown once in a while rather than for every caption.
     */
    notifyCaptionError(message) {
        const now = Date.now();
        if (now - (this.captionErrorShownAt[message] || 0) < CAPTION_ERROR_INTERVAL * 1000) {
            return;
        }
        this.captionErrorShownAt[message] = now;
        this.notification?.add(message, { type: "warning", sticky: false });
    }

    /**
     * Settle on the speaker's language: detecting it costs as much as transcribing, so once
     * it is known it is sent along and only checked again every few captions.
     */
    updateLanguage({ text, language, language_probability }, detected) {
        if (!detected) {
            this.lockedCaptions++;
            return;
        }
        if (!language) {
            return;
        }
        const streak = this.languageStreak;
        this.languageStreak = {
            language,
            count: streak.language === language ? streak.count + 1 : 1,
        };
        const confident =
            language_probability >= LANGUAGE_LOCK_PROBABILITY &&
            text.length >= LANGUAGE_LOCK_MIN_CHARS;
        if (confident || this.languageStreak.count >= LANGUAGE_STREAK) {
            this.lockedLanguage = language;
            this.lockedCaptions = 0;
        }
        // otherwise a re-check that disagrees keeps detecting until two captions agree
    }

    /** Release the microphone and drop audio not sent yet. */
    stopCapture() {
        this.captureAttempt++; // a start still awaiting the browser gives up
        this.state.isListening = false;
        this.state.isStreamingAudio = false;

        if (this.captureNode) {
            this.captureNode.port.onmessage = null;
            this.captureNode.disconnect();
            this.captureNode = null;
        }
        if (this.sourceNode) {
            this.sourceNode.disconnect();
            this.sourceNode = null;
        }
        if (this.filterNode) {
            this.filterNode.disconnect();
            this.filterNode = null;
        }
        if (this.audioContext) {
            this.audioContext.close().catch(() => {});
            this.audioContext = null;
        }
        if (this.stream) {
            this.stream.getTracks().forEach((t) => t.stop());
            this.stream = null;
        }
        this.segmenter = null;
        this.pending = [];
    }

    resetMeeting() {
        this.stopCapture();
        this.micUnavailable = false;
        this.state.transcribeEnabled = false;
        this.state.subtitlesActive = false;
        this.state.activeSubtitles = [];
        this.state.meetingStartTime = null;
        this.state.activeChannelId = null;
        this.state.subtitlesEnabled = false;
        this.lockedLanguage = null;
        this.languageStreak = { language: null, count: 0 };
        this.lockedCaptions = 0;
    }

    getDurationMinutes() {
        if (!this.state.meetingStartTime) {
            return 1;
        }
        const diffMs = Date.now() - this.state.meetingStartTime;
        return Math.max(1, Math.round(diffMs / 60000));
    }
}

export const meetingSpeechService = {
    dependencies: ["bus_service", "notification", "mail.store"],
    start(env, services) {
        return new MeetingSpeechService(env, services);
    },
};

registry.category("services").add("discuss_meeting_ai.speech", meetingSpeechService);
