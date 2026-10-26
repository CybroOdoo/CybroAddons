/** @odoo-module **/
import { Component, xml, signal, proxy, onMounted, onWillUnmount } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { registerComposerAction } from "@mail/core/common/composer_actions";
import { markEventHandled } from "@web/core/utils/misc";

export class CameraDialog extends Component {
    static template = xml`
        <Dialog size="'lg'" title="'Camera'" contentClass="'o_camera_dialog_wrapper'">
            <div class="o_camera_dialog">
                <t t-if="this.state.status === 'pending'">
                    <div class="o_camera_status_msg text-center p-4">
                        <i class="fa fa-circle-o-notch fa-spin fa-3x mb-3 text-primary"/>
                        <p class="text-muted">Waiting for camera permissions...</p>
                    </div>
                </t>
                <t t-if="this.state.status === 'loading'">
                    <div class="o_camera_status_msg text-center p-4">
                        <i class="fa fa-spinner fa-spin fa-3x mb-3 text-primary"/>
                        <p class="text-muted">Loading camera...</p>
                    </div>
                </t>
                <t t-if="this.state.status === 'error'">
                    <div class="o_camera_status_msg text-center p-4">
                        <i class="fa fa-exclamation-triangle fa-3x mb-3 text-warning"/>
                        <p class="text-danger fw-semibold" t-out="this.state.errorMessage"/>
                    </div>
                </t>
                <t t-if="this.state.status === 'capturing'">
                    <div class="o_camera_status_msg text-center p-4">
                        <i class="fa fa-spinner fa-spin fa-3x mb-3 text-primary"/>
                        <p class="text-muted">Uploading image, please wait...</p>
                    </div>
                </t>
                <video
                    t-ref="this.videoCamRef"
                    t-att-class="{ 'd-none': this.state.status !== 'ready' }"
                    autoplay="true"
                    playsinline="true"
                    style="width:100%; border-radius:4px;"
                />
                <canvas t-ref="this.canvasRef" width="640" height="480" style="display:none;"/>
            </div>
            <t t-set-slot="footer">
                <button
                    class="btn btn-primary"
                    t-on-click="this.imageCapture"
                    t-att-disabled="this.state.status !== 'ready'"
                >
                    <i class="fa fa-camera me-1"/>
                    Capture
                </button>
                <button class="btn btn-secondary" t-on-click="this.onClickCancel">Close</button>
            </t>
        </Dialog>
    `;

    static components = { Dialog };
    static props = {
        close: Function,
        uploadFile: Function,
    };

    videoCamRef = signal.ref();
    canvasRef = signal.ref();

    setup() {
        this.vidStream = null;
        this.state = proxy({
            // 'pending'   → waiting for permission prompt
            // 'loading'   → permission granted, camera feed initializing
            // 'ready'     → camera live, capture allowed
            // 'error'     → permission denied or not supported
            // 'capturing' → upload in progress, button locked
            status: 'pending',
            errorMessage: '',
        });

        onMounted(async () => {
            try {
                const mediaDevices = navigator.mediaDevices;
                if (!mediaDevices || !mediaDevices.getUserMedia) {
                    throw new Error(_t("Media devices not supported in this browser."));
                }

                // If permission is already granted, skip the 'pending' screen
                // and go straight to 'loading' before getUserMedia is called
                try {
                    const permissionStatus = await navigator.permissions.query({ name: 'camera' });
                    if (permissionStatus.state === 'granted') {
                        this.state.status = 'loading';
                    }
                } catch {
                    // navigator.permissions not supported — stay on 'pending'
                }

                this.vidStream = await mediaDevices.getUserMedia({
                    audio: false,
                    video: { width: 1280, height: 720 },
                });

                // Permission granted (may have just been accepted) — ensure loading state
                this.state.status = 'loading';

                const video = this.videoCamRef();
                if (video) {
                    if ("srcObject" in video) {
                        video.srcObject = this.vidStream;
                    } else {
                        video.src = window.URL.createObjectURL(this.vidStream);
                    }
                    video.onloadedmetadata = () => {
                        video.play();
                        this.state.status = 'ready';
                    };
                }
            } catch {
                this.state.status = 'error';
                this.state.errorMessage = _t(
                    "Camera access is not available. Please check your permissions."
                );
            }
        });

        onWillUnmount(() => {
            this.stopCamera();
        });
    }

    stopCamera() {
        if (this.vidStream) {
            this.vidStream.getTracks().forEach((track) => track.stop());
            this.vidStream = null;
        }
    }

    async imageCapture() {
        if (this.state.status !== 'ready') return;
        this.state.status = 'capturing';

        const canvas = this.canvasRef();
        const video = this.videoCamRef();

        if (!canvas || !video) {
            this.state.status = 'ready';
            return;
        }

        try {
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);

            const image_data_url = canvas.toDataURL('image/jpeg', 0.92);
            const arr = image_data_url.split(',');
            const mime = arr[0].match(/:(.*?);/)[1];
            const bstr = atob(arr[1]);
            let n = bstr.length;
            const u8arr = new Uint8Array(n);
            while (n--) {
                u8arr[n] = bstr.charCodeAt(n);
            }

            // crypto.randomUUID() guarantees a globally unique filename
            // even when multiple users capture at the exact same millisecond
            const file = new File([u8arr], `camera_${crypto.randomUUID()}.jpeg`, { type: mime });

            await this.props.uploadFile(file);

            this.stopCamera();
            this.props.close();
        } catch {
            this.state.status = 'ready';
        }
    }

    onClickCancel() {
        this.stopCamera();
        this.props.close();
    }
}

registerComposerAction("add-camera-image", {
    icon: "photo_camera",
    name: _t("Camera"),
    onSelected: ({ owner }, ev) => {
        markEventHandled(ev, "composer.onClickCamera");
        owner.env.services.dialog.add(CameraDialog, {
            uploadFile: async (file) => {
                await owner.attachmentUploader.uploadFile(file);
            },
        });
    },
    sequence: 25,
});