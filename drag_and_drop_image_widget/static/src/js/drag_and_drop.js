/** @odoo-module **/

import { isMobileOS } from "@web/core/browser/feature_detection";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { imageUrl } from "@web/core/utils/urls";
import { FileUploader } from "@web/views/fields/file_handler";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, proxy, signal, onWillUpdateProps, onMounted, useProps, t } from "@odoo/owl";

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
    if (typeof value === "string") {
        return value;
    }
    return "";
}

export const dragAndDropBinaryFieldProps = {
    ...standardFieldProps,
    alt: t.string().optional(),
    enableZoom: t.boolean().optional(),
    imgClass: t.string().optional(""),
    zoomDelay: t.number().optional(),
    previewImage: t.string().optional(),
    acceptedFileExtensions: t.string().optional("image/*"),
    width: t.number().optional(),
    height: t.number().optional(),
    reload: t.boolean().optional(true),
};

export class DragAndDropBinaryField extends Component {
    static template = "drag_and_drop_image_widget.DragAndDropField";
    static components = {
        FileUploader,
    };
    props = useProps(dragAndDropBinaryFieldProps);

    rootRef = signal.ref();
    inputFile = signal.ref();
    image_picker = signal.ref();
    droptarget = signal.ref();
    dropimg = signal.ref();

    setup() {
        this.notification = useService("notification");
        this.isMobile = isMobileOS();
        this.state = proxy({
            isValid: true,
        });
        this.rawCacheKey = this.props.record.data.write_date;
        this.lastURL = null;
        this.pendingFile = null;

        onWillUpdateProps((nextProps) => {
            const { record } = this.props;
            const { record: nextRecord } = nextProps;
            if (record.resId !== nextRecord.resId || nextRecord.mode === "readonly") {
                this.rawCacheKey = nextRecord.data.write_date;
            }
        });

        onMounted(() => this.setupDragAndDrop());
    }

    isAcceptedFile(file) {
        if (!file || !file.type) {
            return false;
        }
        if (!file.type.startsWith("image/")) {
            return false;
        }
        const accepted = this.props.acceptedFileExtensions;
        if (!accepted || accepted === "image/*" || accepted === "*") {
            return true;
        }
        const extensions = accepted.split(",").map((ext) => ext.trim().toLowerCase());
        const fileName = (file.name || "").toLowerCase();
        const fileType = (file.type || "").toLowerCase();
        return extensions.some((ext) => {
            if (ext.startsWith(".")) {
                return fileName.endsWith(ext);
            }
            if (ext.endsWith("/*")) {
                const baseType = ext.slice(0, -2);
                return fileType.startsWith(baseType);
            }
            return fileType === ext;
        });
    }

    processFile(file) {
        if (!file) {
            return;
        }
        if (!this.isAcceptedFile(file)) {
            this.notification.add(_t("Selected file is not an accepted image format."), {
                type: "warning",
            });
            return;
        }

        const reader = new FileReader();
        reader.onload = (event) => {
            const result = event.target.result;
            const dropimgEl = this.dropimg();
            const inputFileEl = this.inputFile();
            if (dropimgEl) {
                dropimgEl.style.backgroundImage = `url(${result})`;
            }
            if (inputFileEl) {
                inputFileEl.value = result;
            }
            this.pendingFile = {
                name: file.name,
                type: file.type,
                data: result.split(",")[1],
                dataUrl: result,
            };
        };
        reader.readAsDataURL(file);
    }

    setupDragAndDrop() {
        const rootEl = this.rootRef();
        const droptarget = this.droptarget();

        if (rootEl && !this.props.readonly) {
            rootEl.addEventListener("dragover", (e) => {
                e.preventDefault();
                const imagePickerEl = this.image_picker();
                if (imagePickerEl) {
                    imagePickerEl.classList.remove("d-none");
                }
                droptarget?.classList.add("dropping");
            });
            rootEl.addEventListener("dragleave", (e) => {
                e.preventDefault();
                droptarget?.classList.remove("dropping");
            });
            rootEl.addEventListener("drop", (e) => {
                e.preventDefault();
                droptarget?.classList.remove("dropping");
                droptarget?.classList.add("dropped");
                const file = e.dataTransfer?.files?.[0];
                if (file) {
                    this.processFile(file);
                }
            });
        }

        if (droptarget) {
            droptarget.addEventListener("dragover", (e) => {
                e.preventDefault();
                droptarget.classList.add("dropping");
            });
            droptarget.addEventListener("dragleave", (e) => {
                e.preventDefault();
                droptarget.classList.remove("dropping");
            });
            droptarget.addEventListener("dragend", (e) => {
                e.preventDefault();
                droptarget.classList.remove("dropping");
            });
            droptarget.addEventListener("drop", (e) => {
                e.preventDefault();
                droptarget.classList.remove("dropping");
                droptarget.classList.add("dropped");

                const file = e.dataTransfer?.files?.[0];
                if (file) {
                    this.processFile(file);
                }
            });
        }
    }

    onDropInputChange(ev) {
        const file = ev.target.files && ev.target.files[0];
        if (file) {
            this.processFile(file);
        }
    }

    get fieldType() {
        return this.props.record.fields[this.props.name]?.type || "binary";
    }

    get containerClass() {
        let containerClass =
            "o_image_uploader_container position-absolute d-flex justify-content-between w-100 bottom-0 opacity-0 opacity-100-hover";
        if (this.isMobile) {
            containerClass += " o_mobile_controls";
        }
        return containerClass;
    }

    get imgAlt() {
        if (this.fieldType === "many2one" && this.props.record.data[this.props.name]) {
            return this.props.record.data[this.props.name].display_name;
        }
        return this.props.alt || _t("Binary file");
    }

    get imgClass() {
        const customClass = this.props.imgClass || "";
        return ["img", "img-fluid"].concat(customClass.split(" ").filter(Boolean)).join(" ");
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
        return Boolean(
            this.props.enableZoom && this.props.record.data[this.props.name]
        );
    }

    get tooltipAttributes() {
        const fieldName = this.fieldType === "many2one" ? this.props.previewImage : this.props.name;
        return {
            template: "web.ImageZoomTooltip",
            info: JSON.stringify({ url: this.getUrl(fieldName) }),
        };
    }

    getUrl(previewFieldName) {
        if (!this.rawCacheKey) {
            this.rawCacheKey = this.props.record.data.write_date;
        }
        if (!this.props.record.data[this.props.name] || !this.state.isValid) {
            return placeholder;
        }
        const fieldName = previewFieldName || this.props.name;
        const data = this.props.record.data[fieldName] || this.props.record.data[this.props.name];

        if (data && typeof data === "object" && data.content) {
            const content = data.content;
            const magic = fileTypeMagicWordMap[content[0]] || "png";
            this.lastURL = `data:image/${magic};base64,${content}`;
            return this.lastURL;
        }

        if (typeof data === "string") {
            if (data.startsWith("data:") || data.startsWith("http://") || data.startsWith("https://") || data.startsWith("/")) {
                this.lastURL = data;
                return this.lastURL;
            }
            if (data.length > 200 && !data.includes(" ")) {
                const magic = fileTypeMagicWordMap[data[0]] || "png";
                this.lastURL = `data:image/${magic};base64,${data}`;
                return this.lastURL;
            }
        }

        this.lastURL = imageUrl(
            this.props.record.resModel,
            this.props.record.resId,
            fieldName,
            { unique: imageCacheKey(this.rawCacheKey) }
        );
        return this.lastURL;
    }

    async onFileRemove() {
        this.state.isValid = true;
        const { previewImage, record } = this.props;
        const changes = { [this.props.name]: false };
        if (previewImage && previewImage !== this.props.name && previewImage in record.fields) {
            changes[previewImage] = false;
        }
        await record.update(changes);
    }

    async onFileUploaded(info) {
        this.rawCacheKey = null;
        this.state.isValid = true;
        const { previewImage, record } = this.props;
        const payload = info ? {
            filename: info?.name || "",
            content: info?.data || info,
        } : false;
        const changes = { [this.props.name]: payload };
        if (previewImage && previewImage !== this.props.name && previewImage in record.fields) {
            changes[previewImage] = payload;
        }
        await record.update(changes);
    }

    onLoadFailed() {
        this.state.isValid = false;
        this.notification.add(_t("Could not display the selected image"), {
            type: "danger",
        });
    }

    async onImageUpload() {
        const inputFileEl = this.inputFile();
        const pending = this.pendingFile;
        const fileDataUrl = inputFileEl?.value || pending?.dataUrl || "";

        if (pending || fileDataUrl) {
            const base64Data = pending?.data || (fileDataUrl.includes(",") ? fileDataUrl.split(",")[1] : fileDataUrl);
            const fileName = pending?.name || "uploaded_image.png";
            const fileType = pending?.type || "image/png";

            await this.onFileUploaded({
                name: fileName,
                type: fileType,
                data: base64Data,
            });
        }

        this.onCloseImagePicker();
    }

    onCloseImagePicker() {
        const imagePickerEl = this.image_picker();
        const dropimgEl = this.dropimg();
        const inputFileEl = this.inputFile();
        const droptarget = this.droptarget();
        if (imagePickerEl) {
            imagePickerEl.classList.add("d-none");
        }
        if (dropimgEl) {
            dropimgEl.style.backgroundImage = "";
        }
        if (inputFileEl) {
            inputFileEl.value = "";
        }
        if (droptarget) {
            droptarget.classList.remove("dropping", "dropped");
        }
        this.pendingFile = null;
    }

    onFileDragImage() {
        const imagePickerEl = this.image_picker();
        if (imagePickerEl) {
            imagePickerEl.classList.remove("d-none");
        }
    }
}

export const dragAndDropBinaryField = {
    component: DragAndDropBinaryField,
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
    fieldDependencies: ({ options }) => {
        const deps = [{ name: "write_date", type: "datetime" }];
        if (options.preview_image) {
            deps.push({ name: options.preview_image });
        }
        return deps;
    },
    isEmpty: () => false,
    extractProps: ({ attrs, options }) => ({
        alt: attrs.alt,
        enableZoom: options.zoom,
        imgClass: options.img_class,
        zoomDelay: options.zoom_delay,
        previewImage: options.preview_image,
        acceptedFileExtensions: options.accepted_file_extensions,
        width: options.size && Boolean(options.size[0]) ? options.size[0] : attrs.width,
        height: options.size && Boolean(options.size[1]) ? options.size[1] : attrs.height,
        reload: "reload" in options ? Boolean(options.reload) : true,
    }),
};

registry.category("fields").add("drag_and_drop", dragAndDropBinaryField);
