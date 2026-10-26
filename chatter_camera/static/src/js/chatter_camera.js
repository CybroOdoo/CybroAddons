import { Chatter } from "@mail/chatter/web_portal_project/chatter";
import { patch } from "@web/core/utils/patch";
import { Component, onMounted, onWillUnmount, signal, useProps, t } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

/**
 * CameraDialog provides a centered, modal dialog for webcam capture
 * using Odoo's native Dialog component.
 */
export class CameraDialog extends Component {
    static template = "chatter_camera.CameraDialog";
    static components = { Dialog };
    props = useProps({
        onCapture: t.function(),
        close: t.function(),
    });

    videoRef = signal.ref();
    canvasRef = signal.ref();

    setup() {
        this.currentStream = null;
        this.notification = useService("notification");

        onMounted(() => {
            this.startCamera();
        });

        onWillUnmount(() => {
            this.stopCamera();
        });
    }

    notify(message, type = "warning") {
        if (this.notification) {
            this.notification.add(message, { type });
        } else if (this.env.services?.notification) {
            this.env.services.notification.add(message, { type });
        }
    }

    get title() {
        return _t("Camera");
    }

    async startCamera() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.notify(_t("Camera access is not supported in this browser or requires an HTTPS connection."));
            this.props.close();
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: false,
                video: {
                    facingMode: "user",
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                },
            });
            this.currentStream = stream;
            const video = this.videoRef();
            if (video) {
                video.srcObject = stream;
                video.onloadedmetadata = () => {
                    video.play();
                };
            }
        } catch (err) {
            this.notify(_t("Unable to access camera: ") + (err ? err.message : ""), "danger");
            this.props.close();
        }
    }

    stopCamera() {
        if (this.currentStream) {
            this.currentStream.getTracks().forEach((track) => track.stop());
            this.currentStream = null;
        }
    }

    capturePhoto() {
        const video = this.videoRef();
        const canvas = this.canvasRef();
        if (!video || !canvas) {
            return;
        }

        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;

        const ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob((blob) => {
            if (blob) {
                const file = new File([blob], `capture_${Date.now()}.jpeg`, {
                    type: "image/jpeg",
                });
                this.props.onCapture(file);
            }
            this.props.close();
        }, "image/jpeg", 0.95);
    }
}

// Patch Chatter to open CameraDialog and upload captured image
patch(Chatter.prototype, {
    onClickCamera() {
        const dialogService = this.dialog || this.env.services.dialog;
        dialogService.add(CameraDialog, {
            onCapture: async (file) => {
                if (!this.state.thread || !this.state.thread.id) {
                    if (this.webChatterProps && this.webChatterProps.saveRecord) {
                        const saved = await this.webChatterProps.saveRecord();
                        if (!saved) {
                            return;
                        }
                    }
                }

                if (this.attachmentUploader) {
                    await this.attachmentUploader.uploadFile(file);
                    if (this.hasParentReloadOnAttachmentsChanged) {
                        this.reloadParentView();
                    }
                    if (this.CHATTER_PANEL) {
                        this.state.activePanel = this.CHATTER_PANEL.ATTACHMENT;
                    }
                }
            },
        });
    },
});
