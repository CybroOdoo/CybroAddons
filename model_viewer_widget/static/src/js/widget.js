import { loadJS } from "@web/core/assets";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { imageUrl } from "@web/core/utils/urls";
import { ImageField, imageField } from "@web/views/fields/image/image_field";
import { onWillDestroy, onWillStart, signal, useEffect } from "@odoo/owl";

const DEFAULT_MODEL = "/model_viewer_widget/static/src/assets/3d.glb";
const VIEW3D_LIBRARY = "/model_viewer_widget/static/lib/view3d/view3d.pkgd.min.js";
// Start of a GLB file encoded in base64: "glTF" and the version 2
const GLB_SIGNATURE = "Z2xURg";

/**
 * Show a GLB file in an interactive 3D viewer. A sample model is displayed
 * as long as the record has no file.
 */
export class Field3D extends ImageField {
    static template = "model_viewer_widget.Field3D";
    viewerRef = signal.ref();

    setup() {
        super.setup();
        this.state.hasLoadFailed = false;
        onWillStart(() => loadJS(VIEW3D_LIBRARY));
        useEffect(() => {
            const el = this.viewerRef();
            const url = this.modelUrl;
            if (el) {
                this.loadModel(el, url);
            }
        });
        onWillDestroy(() => this.view3D?.destroy());
    }

    get acceptedFileExtensions() {
        return ".glb";
    }

    /**
     * @returns {string} the URL of the model of the current record
     */
    get modelUrl() {
        const { name, record } = this.props;
        const data = record.data[name];
        if (!data) {
            return DEFAULT_MODEL;
        }
        if (data.content) {
            return `data:model/gltf-binary;base64,${data.content}`;
        }
        return imageUrl(record.resModel, record.resId, name, {
            unique: data.checksum || this.rawCacheKey,
        });
    }

    /**
     * @param {HTMLElement} el wrapper of the viewer
     * @param {string} url URL of the model to display
     */
    async loadModel(el, url) {
        if (url === this.loadedUrl) {
            return;
        }
        this.loadedUrl = url;
        this.state.hasLoadFailed = false;
        try {
            if (this.view3D) {
                await this.view3D.load(url);
            } else {
                this.view3D = new window.View3D(el, {
                    src: url,
                    autoInit: false,
                });
                await this.view3D.init();
            }
        } catch {
            this.state.hasLoadFailed = true;
        }
    }

    /**
     * Refuse any file which is not a GLB model.
     *
     * @override
     */
    async onFileUploaded(info) {
        if (!info.name.toLowerCase().endsWith(".glb") || !info.data.startsWith(GLB_SIGNATURE)) {
            this.notification.add(_t("Only GLB 3D models are supported."), {
                type: "danger",
            });
            return;
        }
        await super.onFileUploaded(info);
    }
}

/**
 * View3D also rejects an internal promise when a model cannot be loaded. The
 * widget already reports this failure, so it must not open the error dialog.
 */
function view3dErrorHandler(env, error, originalError) {
    if (originalError?.name !== "View3DError") {
        return false;
    }
    error.unhandledRejectionEvent?.preventDefault();
    return true;
}

export const model3dViewer = {
    ...imageField,
    component: Field3D,
};

registry.category("fields").add("model_3d_viewer", model3dViewer);
registry.category("error_handlers").add("model_3d_viewer", view3dErrorHandler, { sequence: 90 });
