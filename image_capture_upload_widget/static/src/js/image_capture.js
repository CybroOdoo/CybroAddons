import { isMobileOS } from "@web/core/browser/feature_detection";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { imageUrl } from "@web/core/utils/urls";
import { FileUploader } from "@web/views/fields/file_handler";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, onWillUpdateProps, proxy, signal, t, useProps } from "@odoo/owl";

export const fileTypeMagicWordMap = {
    "/": "jpg",
    R: "gif",
    i: "png",
    P: "svg+xml",
    U: "webp",
};

const placeholder = "/web/static/img/placeholder.png";

export const imageCaptureProps = {
    ...standardFieldProps,
    previewImage: t.string().optional(),
    acceptedFileExtensions: t.string().optional("image/*"),
    width: t.number().optional(),
    height: t.number().optional(),
    reload: t.boolean().optional(true),
};

export class ImageCaptureComponent extends Component {
    static template = "image_capture_upload_widget.CaptureImage";
    static components = {
        FileUploader,
    };
    props = useProps(imageCaptureProps);

    player = signal.ref();
    snapshot = signal.ref();
    camera = signal.ref();

    setup() {
        this.notification = useService("notification");
        this.isMobile = isMobileOS();
        this.state = proxy({
            isValid: true,
            stream: null,
            isCameraOpen: false,
            hasSnapshot: false,
        });

        this.rawCacheKey = this.props.record.data.write_date;

        onWillUpdateProps((nextProps) => {
            const { record } = this.props;
            const { record: nextRecord } = nextProps;
            if (record.resId !== nextRecord.resId || nextRecord.mode === "readonly") {
                this.rawCacheKey = nextRecord.data.write_date;
            }
        });
    }

    get playerEl() {
        return this.player() || (this.player && this.player.el);
    }
    get snapshotEl() {
        return this.snapshot() || (this.snapshot && this.snapshot.el);
    }

    get sizeStyle() {
        let style = "";
        if (this.props.width) {
            style += `max-width: ${this.props.width}px;`;
        }
        if (this.props.height) {
            style += `max-height: ${this.props.height}px;`;
        }
        return style;
    }

    getUrl(previewFieldName) {
        if (!this.props.reload && this.lastURL) {
            return this.lastURL;
        }
        if (!this.props.record.data[this.props.name] || !this.state.isValid) {
            return placeholder;
        }

        const value = this.props.record.data[this.props.name];
        const content = typeof value === "object" && value !== null ? value.content : value;

        if (typeof content === "string") {
            if (content.startsWith("data:")) {
                this.lastURL = content;
                return this.lastURL;
            }
            const magic = fileTypeMagicWordMap[content[0]];
            if (magic || !this.props.record.resId || this.rawCacheKey === null) {
                this.lastURL = `data:image/${magic || "png"};base64,${content}`;
                return this.lastURL;
            }
        }

        const fieldName = (previewFieldName && this.props.record.data[previewFieldName]) ? previewFieldName : this.props.name;
        this.lastURL = imageUrl(
            this.props.record.resModel,
            this.props.record.resId,
            fieldName,
            { unique: this.rawCacheKey || this.props.record.data.write_date }
        );
        return this.lastURL;
    }

    onFileRemove() {
        this.state.isValid = true;
        this.lastURL = null;
        this.rawCacheKey = null;
        this.props.record.update({ [this.props.name]: false });
    }

    async onFileUploaded(info) {
        this.state.isValid = true;
        this.rawCacheKey = null;
        this.lastURL = null;
        const payload = info ? (info.data || info) : false;
        this.props.record.update({ [this.props.name]: payload });
    }

    async onClickOpenCamera() {
        try {
            this.state.isCameraOpen = true;
            this.state.hasSnapshot = false;
            this.state.stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            if (this.playerEl) {
                this.playerEl.srcObject = this.state.stream;
            }
        } catch (error) {
            this.notification.add(_t("Could not access camera: ") + error.message, { type: "danger" });
            this.stopCamera();
        }
    }

    stopTracksOnMediaStream(mediaStream) {
        if (mediaStream) {
            for (const track of mediaStream.getTracks()) {
                track.stop();
            }
        }
    }

    stopCamera() {
        if (this.state.stream) {
            this.stopTracksOnMediaStream(this.state.stream);
            this.state.stream = null;
        }
        if (this.playerEl) {
            this.playerEl.srcObject = null;
        }
        this.state.isCameraOpen = false;
        this.state.hasSnapshot = false;
    }

    onClickCaptureImage() {
        const canvas = this.snapshotEl;
        const video = this.playerEl;
        if (!canvas || !video) return;

        const context = canvas.getContext('2d');
        canvas.width = video.videoWidth || 320;
        canvas.height = video.videoHeight || 240;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        this.capturedUrl = canvas.toDataURL('image/png');
        this.state.hasSnapshot = true;
    }

    async onClickSaveImage() {
        try {
            if (this.capturedUrl) {
                const base64Data = this.capturedUrl.split(',')[1];
                await this.onFileUploaded(base64Data);
            }
        } catch (error) {
            this.notification.add(_t("Error saving captured image"), { type: "danger" });
        }
        this.stopCamera();
    }

    onLoadFailed() {
        this.state.isValid = false;
    }
}

export const imageCapture = {
    component: ImageCaptureComponent,
    displayName: _t("Image Capture"),
    supportedTypes: ["binary"],
    fieldDependencies: [{ name: "write_date", type: "datetime" }],
    isEmpty: () => false,
    extractProps: ({ attrs, options }) => ({
        previewImage: options.preview_image,
        acceptedFileExtensions: options.accepted_file_extensions || "image/*",
        width: options.size && Boolean(options.size[0]) ? options.size[0] : attrs.width,
        height: options.size && Boolean(options.size[1]) ? options.size[1] : attrs.height,
        reload: "reload" in options ? Boolean(options.reload) : true,
    }),
};

registry.category("fields").add("capture_image", imageCapture);
