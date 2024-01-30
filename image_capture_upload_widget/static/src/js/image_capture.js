/** @odoo-module **/

import { isMobileOS } from "@web/core/browser/feature_detection";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { url } from "@web/core/utils/urls";
import { isBinarySize } from "@web/core/utils/binary";
import { jsonrpc } from "@web/core/network/rpc_service";
import { FileUploader } from "@web/views/fields/file_handler";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState, onWillUpdateProps,useRef} from "@odoo/owl";
const { DateTime } = luxon;
export const fileTypeMagicWordMap = {
    "/": "jpg",
    R: "gif",
    i: "png",
    P: "svg+xml",
};

const placeholder = "/web/static/img/placeholder.png";
export function imageCacheKey(value) {
    if (value instanceof DateTime) {
        return value.ts;
    }
    return "";
}
class imageCapture extends Component {
 static template = "CaptureImage";
    static components = {
       FileUploader,};
    static props = {
         ...standardFieldProps,
        enableZoom: { type: Boolean, optional: true },
        zoomDelay: { type: Number, optional: true },
        previewImage: { type: String, optional: true },
        acceptedFileExtensions: { type: String, optional: true },
        width: { type: Number, optional: true },
        height: { type: Number, optional: true },
        reload: { type: Boolean, optional: true },
    };
    static defaultProps = {
             acceptedFileExtensions: "image/*",
        reload: true,
    };
    setup() {
        this.notification = useService("notification");
          this.orm = useService("orm")
        this.isMobile = isMobileOS();
        this.state = useState({
            isValid: true,
            stream: null,

        });
         this.player = useRef("player");
         this.capture = useRef("capture");
         this.camera = useRef("camera");
         this.save_image = useRef("save_image");
       this.rawCacheKey = this.props.record.data.write_date;
        onWillUpdateProps((nextProps) => {
            const { record } = this.props;
            const { record: nextRecord } = nextProps;
            if (record.resId !== nextRecord.resId || nextRecord.mode === "readonly") {
                this.rawCacheKey = nextRecord.data.write_date;
            }
        });
    }

    get sizeStyle() {
        // For getting image style details
        let style = "";
        if (this.props.width) {
            style += `max-width: ${this.props.width}px;`;
        }
        if (this.props.height) {
            style += `max-height: ${this.props.height}px;`;
        }
        return style;
    }
    get hasTooltip() {
    return (
            this.props.enableZoom && this.props.readonly && this.props.record.data[this.props.name]
        );
    }
    getUrl(previewFieldName) {
        // getting the details and url of the image
        if (!this.props.reload && this.lastURL) {
            return this.lastURL;
        }
        if (this.state.isValid && this.props.record.data[this.props.name]) {
            if (isBinarySize(this.props.record.data[this.props.name])) {
                if (!this.rawCacheKey) {
                    this.rawCacheKey = this.props.record.data.write_date;
                }
                this.lastURL = url("/web/image", {
                    model: this.props.record.resModel,
                    id: this.props.record.resId,
                    field: previewFieldName,
                    unique: imageCacheKey(this.rawCacheKey),
                });
            } else {
                // Use magic-word technique for detecting image type
                 const magic =
                    fileTypeMagicWordMap[this.props.record.data[this.props.name][0]] || "png";
                this.lastURL = `data:image/${magic};base64,${
                    this.props.record.data[this.props.name]
                }`;
            }
            return this.lastURL;
        }
        return placeholder;
    }
    onFileRemove() {
        // removing the images
        this.state.isValid = true;
           this.props.record.update({ [this.props.name]: false });
    }
     async onFileUploaded(info) {
        // Upload the images
        this.state.isValid = true;
        this.rawCacheKey = null;
        this.props.record.update({ [this.props.name]: info.data });
    }
    onFileCaptureImage() {
        // Open a window for open the image and capture it
        var field = this.props.name;
        var id = this.props.record.data.id;
        var model = this.props.record.resModel;
    }
    async OnClickOpenCamera() {
        // opening the camera for capture the image
        this.player.el.classList.remove('d-none');
        this.capture.el.classList.remove('d-none');
        this.camera.el.classList.add('d-none');
        this.state.stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
	    this.player.el.srcObject = this.state.stream;
    }
    stopTracksOnMediaStream(mediaStream) {
        for (const track of mediaStream.getTracks()) {
            track.stop();
        }
    }
    async OnClickCaptureImage() {
        // Capture the image from webcam and close the webcam
        var context = snapshot.getContext('2d');
        var canvas = document.getElementById('snapshot')
        var image = document.getElementById('image');
        this.save_image.el.classList.remove('d-none');
        context.drawImage(player, 0, 0, 320, 240);
        image.value = context.canvas.toDataURL();
        canvas.classList.remove('d-none');
        this.url = context.canvas.toDataURL();
    }
    async OnClickSaveImage(){
        // Saving the image to that field
        var self = this
         await jsonrpc('/web/dataset/call_kw', {
            model: 'image.capture',
            method: 'action_save_image',
            args: [[], this.url],
            kwargs: {}
        }).then(function(results){
            self.props.value = results
            var data = {
                    data:  results,
                    name : "ImageFile.png",
                    objectUrl: null,
                    size : 106252,
                    type: "image/png"
                }
            self.onFileUploaded(data)
        })
        this.player.el.classList.add('d-none');
        var snapshot = document.getElementById('snapshot')
        snapshot.classList.add('d-none');
        this.capture.el.classList.add('d-none');
        this.save_image.el.classList.add('d-none');
        this.camera.el.classList.remove('d-none');
         this.player.el.srcObject = null;
        if (!this.state.stream) {
            return;
        }
        this.stopTracksOnMediaStream(this.state.stream);
        this.state.stream = null;
    }
    onLoadFailed() {
        this.state.isValid = false;
        this.notification.add(this.env._t("Could not display the selected image"), {
            type: "danger",
        });
    }
}
export const ImageCapture = {
    component: imageCapture,
     displayName: _t("Image"),
      supportedOptions: [
        {
            label: _t("Reload"),
            name: "reload",
            type: "boolean",
            default: true,
        },
        {
            label: _t("Enable zoom"),
            name: "zoom",
            type: "boolean",
        },
        {
            label: _t("Zoom delay"),
            name: "zoom_delay",
            type: "number",
            help: _t("Delay the apparition of the zoomed image with a value in milliseconds"),
        },
        {
            label: _t("Accepted file extensions"),
            name: "accepted_file_extensions",
            type: "string",
        },
        {
            label: _t("Size"),
            name: "size",
            type: "selection",
            choices: [
                { label: _t("Small"), value: "[0,90]" },
                { label: _t("Medium"), value: "[0,180]" },
                { label: _t("Large"), value: "[0,270]" },
            ],
        },
        {
            label: _t("Preview image"),
            name: "preview_image",
            type: "field",
            availableTypes: ["binary"],
        },
    ],
supportedTypes: ["binary"],
    fieldDependencies: [{ name: "write_date", type: "datetime" }],
    isEmpty: () => false,
    extractProps: ({ attrs, options }) => ({
        enableZoom: options.zoom,
        zoomDelay: options.zoom_delay,
        previewImage: options.preview_image,
        acceptedFileExtensions: options.accepted_file_extensions,
        width: options.size && Boolean(options.size[0]) ? options.size[0] : attrs.width,
        height: options.size && Boolean(options.size[1]) ? options.size[1] : attrs.height,
        reload: "reload" in options ? Boolean(options.reload) : true,
    }),
};
registry.category("fields").add("capture_image", ImageCapture);