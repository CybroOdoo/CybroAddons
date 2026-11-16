/** @odoo-module **/
import { Component, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
//Video button systray
class VideoButton extends Component {
    static template = "odoo_screen_recording.ScreenCaptureSystray";
    setup() {
      super.setup();
      this.state = proxy({
          isRecording: false,
      });
    }
    async _onClick() {
        try {
              let stream = await navigator.mediaDevices.getDisplayMedia({
                video: true,
              });
              this.state.isRecording = true;
              const mime = MediaRecorder.isTypeSupported("video/webm; codecs=vp9")
              ? "video/webm; codecs=vp9"
              : "video/webm";
              let mediaRecorder = new MediaRecorder(stream, {
                mimeType: mime,
              });
              let chunks = [];
              mediaRecorder.addEventListener("dataavailable", (e) => {
                chunks.push(e.data);
              });
              mediaRecorder.addEventListener("stop", async () => {
                this.state.isRecording = false;
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
                const response = await rpc('/web/dataset/call_kw', {
                    model: 'video.store',
                    method: 'video_record',
                    args: [res],
                    kwargs: {},  // Add any keyword arguments if required
                });
              });
              mediaRecorder.start();
        } catch (e) {
              this.state.isRecording = false;
              // Screen recording was cancelled by user or not supported
        }
    }
}
export const systrayItem = {
    Component: VideoButton,
};
registry.category("systray").add("odoo_screen_recording.video_widget", systrayItem);
