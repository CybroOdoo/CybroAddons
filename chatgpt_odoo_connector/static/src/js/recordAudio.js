/** @odoo-module **/
const { Component, useState, useRef, useExternalListener, xml } = owl;
import { registry } from "@web/core/registry";
import { browser } from '@web/core/browser/browser';
import {_t} from 'web.core';
/* Extending the component and creating class recordAudio */
export class recordAudio extends Component {
    constructor() {
        super(...arguments);
        this.state = useState({
            startedRecording: '',
            transcriptedText: '',
            audioChunks: [],
        });
        this.recordAudio = this.recordAudio.bind(this);
        this.stopRecord = this.stopRecord.bind(this);
        this.onWindowClick = this.onWindowClick.bind(this);
        useExternalListener(window, "click", this.onWindowClick);
    }
    /* Function for recording audio and save the recording in a file. */
    async recordAudio(ev){
        this.state.startedRecording = true
        this.state.audioChunks = [];
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    this.state.audioChunks.push(e.data);
                }
            };

            this.mediaRecorder.onstop = async () => {
                if (this.state.audioChunks.length > 0) {
                    const audioBlob = new Blob(this.state.audioChunks, { type: 'audio/wav' });
                    const file = new File([audioBlob], 'recorded_audio.wav', { type: 'audio/wav' });
                    const formData = new FormData();
                    formData.append('file', file);
                    const response = await fetch('/upload_audio', {
                        method: 'POST',
                        body: formData,
                    });
                    const { filePath } = await response.json();
                    this.state.transcriptedText = await this.props.rpc.query({
                        model: 'open.chatgpt',
                        method: 'convert_to_text',
                        args: [filePath],
                    })
                }
            };

            this.audioStream = stream;
            this.mediaRecorder.start();
        } catch (error) {
            this.props.self.displayNotification({
                title: _t('Warning'),
                message: "Recording Error: Error accessing Microphone"
            });
        }
    }
    /* Function for stop audio recording  */
    async stopRecord() {
        this.state.startedRecording = false;
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
            if (this.audioStream) {
                this.audioStream.getTracks().forEach(track => track.stop());
            }
        }
    }

    /* Function for inserting the converted text from the audio file. */
    Insert(){
        var content = this.state.transcriptedText
        const lines = content.split('\n').filter(line => line.trim().length);
        const fragment = document.createDocumentFragment();
        for (const line of lines) {
            const block = document.createElement(line.startsWith('Title: ') ? 'h2' : 'p');
            block.innerText = line;
            fragment.appendChild(block);
        }
        this.props.self.el.appendChild(fragment);
        this.Cancel()
    }

    /* Function for cancelling it will remove the element popChatGPT*/
    Cancel(){
        var element = document.querySelector('.popChatGPT');
        element.remove();
    }
    /* Function for closing the widget while clicking outside */
    onWindowClick(ev) {
        var element = document.querySelector('.popChatGPT');
        if (element && !element.contains(ev.target)){
            this.Cancel()
        }
    }

}

recordAudio.template = xml`
    <div class="popChatGPT">
        <div style="display: flex; align-items: end;margin-top:-20px;">
            <img src="chatgpt_odoo_connector/static/src/Icons/icon.png" height="35px"/>
            <div class="h2 heading">Speech-to-text</div>
        </div>
        <hr/>
        <div class="mb-3 audio-record">
            <button class="btn btn-success button-mic" t-if="!state.startedRecording"  t-on-click="() => recordAudio(this)">
                <i class="fa fa-microphone" style="font-size: 24px;color:black;"/>
            </button>
            <button class="btn btn-danger button-mic" t-if="state.startedRecording" style="border-radius:13px;" t-on-click="() => stopRecord(this)">
                <i class="fa fa-microphone-slash" style="font-size: 24px;color:black;"></i>
            </button>
        </div>
        <label for="response" class="form-label" t-if="state.transcriptedText"
            style="color:white;">Response</label>
        <div t-if="state.transcriptedText">
            <div class="mb-3">
                <textarea id="response" class="custom-text" rows="4" t-model="state.transcriptedText"></textarea>
            </div>
        </div>
        <div style="display: flex;justify-content: space-around;">
            <button class="btn btn-primary custom" t-if="state.transcriptedText" t-on-click="Insert">Insert</button>
            <button class="btn btn-secondary custom" t-on-click="Cancel">Cancel</button>
        </div>
    </div>`;
registry.category("actions").add("recordAudio", recordAudio);
