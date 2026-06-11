/** @odoo-module **/

import { Component, onWillStart, onWillDestroy, onMounted, useRef, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";

export class CameraDialog extends Component {
    static components = { Dialog };
    static template = "camera_in_discuss.CameraDialog";
    static props = {
        close: Function,
        onCapture: Function,
    };

    setup() {
        this.videoRef = useRef("video");
        this.canvasRef = useRef("canvas");
        this.stream = null;
        this.state = useState({ error: null });

        onWillStart(async () => {
            try {
                this.stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            } catch (err) {
                this.state.error = _t("Could not access camera. Please ensure you have granted permission.");
                console.error("Camera access error:", err);
            }
        });

        onMounted(() => {
            if (this.stream && this.videoRef.el) {
                this.videoRef.el.srcObject = this.stream;
                this.videoRef.el.play();
            }
        });

        onWillDestroy(() => {
            this.stopStream();
        });
    }

    stopStream() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }

    capture() {
        if (!this.videoRef.el || !this.canvasRef.el) return;

        const video = this.videoRef.el;
        const canvas = this.canvasRef.el;

        if (video.videoWidth === 0 || video.videoHeight === 0) {
            console.error("Video dimensions are zero. Camera might not be ready.");
            return;
        }

        const context = canvas.getContext("2d");

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob((blob) => {
            if (!blob) {
                console.error("Canvas toBlob failed.");
                return;
            }
            const file = new File([blob], "image.jpg", { type: "image/jpeg" });
            this.props.onCapture(file);
            this.props.close();
        }, "image/jpeg", 0.9);
    }
}
