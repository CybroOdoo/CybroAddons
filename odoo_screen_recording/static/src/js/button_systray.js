/** @odoo-module **/
import { useState, Component, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { jsonrpc } from "@web/core/network/rpc_service";
//Video button systray
class VideoButton extends Component {
    static template = "odoo_screen_recording.ScreenCaptureSystray";
    setup() {
      super.setup()
      this.icon = useRef('record')
    }
    async _onClick() {
    var icon = this.icon;
        try {
              let stream = await navigator.mediaDevices.getDisplayMedia({
                video: true,
              });
              icon.el.style.color = "#28a745";
              const mime = MediaRecorder.isTypeSupported("video/webm; codecs=vp9")
              ? "video/webm; codecs=vp9"
              : "video/webm";
              let mediaRecorder = new MediaRecorder(stream, {
                mimeType: mime,
              });
              let chunks = [];
              mediaRecorder.addEventListener("dataavailable", function (e) {
                chunks.push(e.data);
              });
              mediaRecorder.addEventListener("stop", async function () {
                icon.el.style.color = "black";
                let blob = new Blob(chunks, {
                    type: chunks[0].type,
                });
                const blobToBase64 = (blob) => {
                    const reader = new FileReader();
                    reader.readAsDataURL(blob);
                    return new Promise((resolve) => {
                        reader.onloadend = () => {
                            resolve(reader.result);
                        };
                    });
                };
                const res = await blobToBase64(blob);
                const response = await jsonrpc('/web/dataset/call_kw', {
                    model: 'video.store',
                    method: 'video_record',
                    args: [res],
                    kwargs: {},  // Add any keyword arguments if required
                });
              });
              mediaRecorder.start();
        } catch (e) {
              console.error("Error:", e);
        }
    }
}
VideoButton.props = {};
export const systrayItem = {
    Component: VideoButton,
};
registry.category("systray").add("odoo_screen_recording.video_widget", systrayItem);
