/** @odoo-module **/

import { isMobileOS } from "@web/core/browser/feature_detection";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { url } from "@web/core/utils/urls";
import { isBinarySize } from "@web/core/utils/binary";
import { FileUploader } from "@web/views/fields/file_handler";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
const { useRef } = owl;
import { onWillUpdateProps } from "@odoo/owl";


import { Component, useState } from "@odoo/owl";
const { DateTime } = luxon;

export const fileTypeMagicWordMap = {
    "/": "jpg",
    R: "gif",
    i: "png",
    P: "svg+xml",
    U: "webp",
};
const placeholder = "/web/static/img/placeholder.png";

export function imageCacheKey(value) {
    if (value instanceof DateTime) {
        return value.ts;
    }
    return "";
}

export class DragAndDropBinaryField extends Component {
    static components = {
        FileUploader,
    };
    static props = {
        ...standardFieldProps,
        enableZoom: {
            type: Boolean,
            optional: true
        },
        zoomDelay: {
            type: Number,
            optional: true
        },
        previewImage: {
            type: String,
            optional: true
        },
        acceptedFileExtensions: {
            type: String,
            optional: true
        },
        width: {
            type: Number,
            optional: true
        },
        height: {
            type: Number,
            optional: true
        },
        reload: {
            type: Boolean,
            optional: true
        },
    };
    static defaultProps = {
        acceptedFileExtensions: "image/*",
        reload: true,
    };

    setup() {
        this.orm = useService('orm');
        this.notification = useService("notification");
        this.orm = useService("orm");
        this.isMobile = isMobileOS();
        this.state = useState({
            isValid: true,
        });
        this.inputFile = useRef('inputFile')
        this.image_picker = useRef('image_picker')
        this.rawCacheKey = this.props.record.data.write_date;
        onWillUpdateProps((nextProps) => {
            const {
                record
            } = this.props;
            const {
                record: nextRecord
            } = nextProps;
            if (record.resId !== nextRecord.resId || nextRecord.mode === "readonly") {
                this.rawCacheKey = nextRecord.data.write_date;
            }
        });
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
    get hasTooltip() {
        return (
            this.props.enableZoom && this.props.readonly && this.props.record.data[this.props.name]
        );
    }

    getUrl(previewFieldName) {
        if (!this.rawCacheKey) {
            this.rawCacheKey = this.props.record.data.write_date;
        }
        if (this.state.isValid && this.props.record.data[this.props.name]) {
            if (isBinarySize(this.props.record.data[this.props.name])) {
                return url("/web/image", {
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
        }
        return placeholder;
    }
    onFileRemove() {
        this.state.isValid = true;
        this.props.record.update({
            [this.props.name]: false
        });
    }
    async onFileUploaded(info) {
        this.rawCacheKey = null;
        this.state.isValid = true;
        if (info.type === "image/webp") {
            // Generate alternate sizes and format for reports.
            const image = document.createElement("img");
            image.src = `data:image/webp;base64,${info.data}`;
            await new Promise((resolve) => image.addEventListener("load", resolve));
            const originalSize = Math.max(image.width, image.height);
            const smallerSizes = [1024, 512, 256, 128].filter((size) => size < originalSize);
            let referenceId = undefined;
            for (const size of [originalSize, ...smallerSizes]) {
                const ratio = size / originalSize;
                const canvas = document.createElement("canvas");
                canvas.width = image.width * ratio;
                canvas.height = image.height * ratio;
                const ctx = canvas.getContext("2d");
                ctx.fillStyle = "rgb(255, 255, 255)";
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(
                    image,
                    0,
                    0,
                    image.width,
                    image.height,
                    0,
                    0,
                    canvas.width,
                    canvas.height
                );
                const [resizedId] = await this.orm.call("ir.attachment", "create_unique", [
                    [{
                        name: info.name,
                        description: size === originalSize ? "" : `resize: ${size}`,
                        datas: size === originalSize ?
                            info.data :
                            canvas.toDataURL("image/webp", 0.75).split(",")[1],
                        res_id: referenceId,
                        res_model: "ir.attachment",
                        mimetype: "image/webp",
                    }, ],
                ]);
                referenceId = referenceId || resizedId; // Keep track of original.
                await this.orm.call("ir.attachment", "create_unique", [
                    [{
                        name: info.name.replace(/\.webp$/, ".jpg"),
                        description: "format: jpeg",
                        datas: canvas.toDataURL("image/jpeg", 0.75).split(",")[1],
                        res_id: resizedId,
                        res_model: "ir.attachment",
                        mimetype: "image/jpeg",
                    }, ],
                ]);
            }
        }
        this.props.record.update({
            [this.props.name]: info.data
        });
    }
    onLoadFailed() {
        this.state.isValid = false;
        this.notification.add(_t("Could not display the selected image"), {
            type: "danger",
        });
    }
    /* Upload Image to the field */
    async onImageUpload() {
        let file = this.inputFile.el.defaultValue
        if (file == "") {
            image_picker.classList.add('d-none');
        } else {
            this.orm.call('ir.attachment', 'action_save_drag_and_drop_image', [
                    [],
                    {
                        'resModel': this.props.record.resModel,
                        'id': this.props.record._config.resId,
                        'name': this.props.name
                    },
                    file
                ])
                .then((result) => {
                    location.reload();
                })
        }
    }
    /* method for dragging */
    onFileDragImage() {
        var image_picker = this.image_picker.el;
        image_picker.classList.remove('d-none');
    }
}
DragAndDropBinaryField.template = 'FieldDragAndDropBinary';
export const dragAndDropBinaryField = {
    component: DragAndDropBinaryField,
    displayName: _t("Image"),
    supportedOptions: [{
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
            choices: [{
                    label: _t("Small"),
                    value: "[0,90]"
                },
                {
                    label: _t("Medium"),
                    value: "[0,180]"
                },
                {
                    label: _t("Large"),
                    value: "[0,270]"
                },
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
    fieldDependencies: [{
        name: "write_date",
        type: "datetime"
    }],
    isEmpty: () => false,
    extractProps: ({
        attrs,
        options
    }) => ({
        enableZoom: options.zoom,
        zoomDelay: options.zoom_delay,
        previewImage: options.preview_image,
        acceptedFileExtensions: options.accepted_file_extensions,
        width: options.size && Boolean(options.size[0]) ? options.size[0] : attrs.width,
        height: options.size && Boolean(options.size[1]) ? options.size[1] : attrs.height,
    }),
};
registry.category("fields").add("drag_and_drop", dragAndDropBinaryField);
