/** @odoo-module **/

import { isMobileOS } from "@web/core/browser/feature_detection";
import { _lt } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { url } from "@web/core/utils/urls";
import { isBinarySize } from "@web/core/utils/binary";
import rpc from 'web.rpc';
import { FileUploader } from "@web/views/fields/file_handler";
import { standardFieldProps } from "@web/views/fields/standard_field_props";


import { Component, useState, onWillUpdateProps } from "@odoo/owl";
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

export class ImageCapture extends Component {
    setup() {
        this.notification = useService("notification");
        this.isMobile = isMobileOS();
        this.state = useState({
            isValid: true,
        });

        this.rawCacheKey = this.props.record.data.__last_update;
        onWillUpdateProps((nextProps) => {
            const { record } = this.props;
            const { record: nextRecord } = nextProps;
            if (record.resId !== nextRecord.resId || nextRecord.mode === "readonly") {
                this.rawCacheKey = nextRecord.data.__last_update;
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
        return this.props.enableZoom && this.props.readonly && this.props.value;
    }

    getUrl(previewFieldName) {
        // getting the details and url of the image
        if (this.state.isValid && this.props.value) {
            if (isBinarySize(this.props.value)) {
                if (!this.rawCacheKey) {
                    this.rawCacheKey = this.props.record.data.__last_update;
                }
                return url("/web/image", {
                    model: this.props.record.resModel,
                    id: this.props.record.resId,
                    field: previewFieldName,
                    unique: imageCacheKey(this.rawCacheKey),
                });
            } else {
                // Use magic-word technique for detecting image type
                const magic = fileTypeMagicWordMap[this.props.value[0]] || "png";
                return `data:image/${magic};base64,${this.props.value}`;
            }
        }
        return placeholder;
    }
    onFileRemove() {
        // removing the images
        this.state.isValid = true;
        this.props.update(false);
    }
    onFileUploaded(info) {
        // Upload the images
        this.state.isValid = true;
        this.rawCacheKey = null;
        this.props.update(info.data);
    }
    onFileCaptureImage() {
        // Open a window for open the image and capture it
        var field = this.props.name;
        var id = this.props.record.data.id;
        var model = this.props.record.resModel;
    }
    async OnClickOpenCamera() {
        // opening the camera for capture the image
        var player = document.getElementById('player');
        var captureButton = document.getElementById('capture');
        var camera = document.getElementById('camera');
        player.classList.remove('d-none');
        captureButton.classList.remove('d-none');
        camera.classList.add('d-none');
        let stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
	    player.srcObject = stream;
    }
    async OnClickCaptureImage() {
        // Capture the image from webcam and close the webcam
        var context = snapshot.getContext('2d');
        var canvas = document.getElementById('snapshot')
        var save_image = document.getElementById('save_image')
        var image = document.getElementById('image');
        var video = document.getElementById('video')
        var camera = document.getElementById('camera');
        save_image.classList.remove('d-none');
        context.drawImage(player, 0, 0, 320, 240);
        image.value = context.canvas.toDataURL();
        canvas.classList.remove('d-none');
        this.url = context.canvas.toDataURL();
        console.log(context.canvas.toDataURL());
        console.log(context);
        console.log(context.getImageData);
    }
    async OnClickSaveImage(){
        // Saving the image to that field
        var self = this;
        rpc.query({
            model: 'image.capture',
            method: 'action_save_image',
            args: [[], this.url],
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
        var player = document.getElementById('player')
        player.classList.add('d-none');
        var snapshot = document.getElementById('snapshot')
        snapshot.classList.add('d-none');
        var capture = document.getElementById('capture')
        capture.classList.add('d-none');
        var save_image = document.getElementById('save_image')
        save_image.classList.add('d-none');
        var camera = document.getElementById('camera')
        camera.classList.remove('d-none');
    }
    onLoadFailed() {
        this.state.isValid = false;
        this.notification.add(this.env._t("Could not display the selected image"), {
            type: "danger",
        });
    }
}

ImageCapture.template = "CaptureImage";
ImageCapture.components = {
    FileUploader,
};
ImageCapture.props = {
    ...standardFieldProps,
    enableZoom: { type: Boolean, optional: true },
    zoomDelay: { type: Number, optional: true },
    previewImage: { type: String, optional: true },
    acceptedFileExtensions: { type: String, optional: true },
    width: { type: Number, optional: true },
    height: { type: Number, optional: true },
};
ImageCapture.defaultProps = {
    acceptedFileExtensions: "image/*",
};

ImageCapture.displayName = _lt("Image");
ImageCapture.supportedTypes = ["binary"];

ImageCapture.fieldDependencies = {
    __last_update: { type: "datetime" },
};

ImageCapture.extractProps = ({ attrs }) => {
    return {
        enableZoom: attrs.options.zoom,
        zoomDelay: attrs.options.zoom_delay,
        previewImage: attrs.options.preview_image,
        acceptedFileExtensions: attrs.options.accepted_file_extensions,
        width:
            attrs.options.size && Boolean(attrs.options.size[0])
                ? attrs.options.size[0]
                : attrs.width,
        height:
            attrs.options.size && Boolean(attrs.options.size[1])
                ? attrs.options.size[1]
                : attrs.height,
    };
};
registry.category("fields").add("capture_image", ImageCapture);
