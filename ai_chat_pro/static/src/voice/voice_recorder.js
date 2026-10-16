import { browser } from "@web/core/browser/browser";

// the sample rate of the audio sent to be turned into text
export const VOICE_SAMPLE_RATE = 16000;
// a voice question is sent when it lasts this long
export const MAX_RECORDING_SECONDS = 60;
// formats tried for voice questions: browsers record only some of them
const RECORDING_TYPES = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];
// the level of the voice (0 to 1) above which someone speaks, and below which it is silent
const SPEECH_LEVEL = 0.08;
const SILENCE_LEVEL = 0.04;
// with an automatic stop: the silence ending a question, and the wait for a first word
const END_SILENCE_MS = 1600;
const NO_SPEECH_MS = 8000;

/**
 * Whether the browser can record the voice: it needs a secure page (https or
 * localhost) and the MediaRecorder API.
 */
export function canRecordVoice() {
    return Boolean(browser.navigator.mediaDevices?.getUserMedia && window.MediaRecorder);
}

export class MicrophoneError extends Error {}

/**
 * Records a voice question from the microphone.
 *
 * ``result`` resolves to the recording (a Blob) once it is stopped: by ``stop()``,
 * after the longest question, or, with ``autoStop``, after the silence that ends a
 * question. It resolves to ``null`` when the recording is cancelled.
 */
export class VoiceRecorder {
    /**
     * @param {Object} [options]
     * @param {Function} [options.onLevel] called with the level of the voice, 0 to 1
     * @param {Function} [options.onSeconds] called each second with the length so far
     * @param {boolean} [options.autoStop] stop after the silence ending a question
     */
    constructor({ onLevel, onSeconds, autoStop = false } = {}) {
        this.onLevel = onLevel;
        this.onSeconds = onSeconds;
        this.autoStop = autoStop;
        this.chunks = [];
        this.discard = false;
        this.isDone = false;
        this.result = new Promise((resolve) => {
            this.resolve = (blob) => {
                this.isDone = true;
                resolve(blob);
            };
        });
    }

    async start() {
        try {
            this.stream = await browser.navigator.mediaDevices.getUserMedia({ audio: true });
        } catch {
            this.resolve(null);
            throw new MicrophoneError();
        }
        if (this.isDone) {
            // cancelled while the browser asked for the microphone
            this.release();
            return;
        }
        try {
            const mimeType = RECORDING_TYPES.find((type) => MediaRecorder.isTypeSupported(type));
            this.recorder = new MediaRecorder(this.stream, mimeType ? { mimeType } : {});
            this.recorder.addEventListener("dataavailable", (ev) => ev.data.size && this.chunks.push(ev.data));
            this.recorder.addEventListener("stop", () => this.onStop());
            this.recorder.start();
        } catch {
            // the browser can not record this microphone: it is released, and nothing is recorded
            this.release();
            this.resolve(null);
            throw new MicrophoneError();
        }
        this.startedAt = Date.now();
        this.seconds = 0;
        this.timer = browser.setInterval(() => {
            this.seconds++;
            this.onSeconds?.(this.seconds);
            if (this.seconds >= MAX_RECORDING_SECONDS) {
                this.stop();
            }
        }, 1000);
        this.listenToLevel();
    }

    /**
     * Measure the level of the voice, to draw it and to hear when the question ends.
     */
    listenToLevel() {
        try {
            this.audioContext = new AudioContext();
            const analyser = this.audioContext.createAnalyser();
            analyser.fftSize = 512;
            this.audioContext.createMediaStreamSource(this.stream).connect(analyser);
            const samples = new Float32Array(analyser.fftSize);
            let spokeAt = 0;
            let silentSince = Date.now();
            const measure = () => {
                if (!this.recorder || this.recorder.state !== "recording") {
                    return;
                }
                analyser.getFloatTimeDomainData(samples);
                let sum = 0;
                for (const sample of samples) {
                    sum += sample * sample;
                }
                // the root mean square, scaled for a voice at a normal distance
                const level = Math.min(1, Math.sqrt(sum / samples.length) * 6);
                this.onLevel?.(level);
                const now = Date.now();
                if (level > SPEECH_LEVEL) {
                    spokeAt = now;
                }
                if (level > SILENCE_LEVEL) {
                    silentSince = now;
                }
                if (this.autoStop) {
                    const endsQuestion = spokeAt && now - silentSince > END_SILENCE_MS;
                    const saysNothing = !spokeAt && now - this.startedAt > NO_SPEECH_MS;
                    if (endsQuestion || saysNothing) {
                        this.stop();
                        return;
                    }
                }
                this.frame = browser.requestAnimationFrame(measure);
            };
            measure();
        } catch {
            // the level is only drawn: recording goes on without it
        }
    }

    stop() {
        if (this.recorder?.state === "recording") {
            this.recorder.stop();
        } else {
            // not recording (yet, or any more): there is nothing to send
            this.release();
            this.resolve(null);
        }
    }

    cancel() {
        this.discard = true;
        this.stop();
    }

    /**
     * Release the microphone, and stop measuring the voice.
     */
    release() {
        browser.clearInterval(this.timer);
        browser.cancelAnimationFrame(this.frame);
        this.stream?.getTracks().forEach((track) => track.stop());
        if (this.audioContext?.state !== "closed") {
            this.audioContext?.close();
        }
        this.onLevel?.(0);
    }

    onStop() {
        this.release();
        if (this.discard || !this.chunks.length) {
            this.resolve(null);
        } else {
            this.resolve(new Blob(this.chunks, { type: this.recorder.mimeType }));
        }
    }
}

/**
 * The recording as 16 kHz mono 16-bit PCM, in base64: the browser decodes the
 * format it records (webm, mp4...), so the server only wraps it in a WAV file, a
 * format all speech to text models read.
 */
export async function toVoiceAudio(blob) {
    const decoder = new AudioContext();
    let decoded;
    try {
        decoded = await decoder.decodeAudioData(await blob.arrayBuffer());
    } finally {
        decoder.close();
    }
    const length = Math.ceil(decoded.duration * VOICE_SAMPLE_RATE);
    // rendering on a single channel mixes the channels, at the sample rate of the context
    const context = new OfflineAudioContext(1, length, VOICE_SAMPLE_RATE);
    const source = context.createBufferSource();
    source.buffer = decoded;
    source.connect(context.destination);
    source.start();
    const samples = (await context.startRendering()).getChannelData(0);
    const pcm = new Int16Array(samples.length);
    for (let i = 0; i < samples.length; i++) {
        const sample = Math.max(-1, Math.min(1, samples[i]));
        pcm[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
    }
    // the bytes of the samples, as a binary string, chunked to stay under the argument limit
    const bytes = new Uint8Array(pcm.buffer);
    let binary = "";
    for (let i = 0; i < bytes.length; i += 0x8000) {
        binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
    }
    return btoa(binary);
}
