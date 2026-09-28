/** @odoo-module **/

import { Component, useState, useRef, onMounted } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

/**
 * Dialog component for selecting or uploading an article cover image.
 *  *
 * Supports three input modes:
 *   - Recent images (cached in localStorage)
 *   - Image URL with preview
 *   - Local file upload
 *  *
 * Emits the chosen base64 image back to the parent via the onSave callback.
 */
export class InfoCoverDialog extends Component {
    static template = "info_hub.InfoCoverDialog";
    static components = { Dialog };

    static props = {
        articleId: { type: Number },
        currentCover: { optional: true },
        onCoverApplied: { type: Function },
        close: { type: Function },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.fileInputRef = useRef("fileInput");

        this.state = useState({

            showUrlPanel: false,

            urlValue: "",

            urlError: "",

            applying: false,
            recentImages: [],
        });
        onMounted(() => {
            this.state.recentImages = this._loadRecent();
        });
    }

    _loadRecent() {
        try {
            const raw = localStorage.getItem("info_hub_recent_covers");
            if (!raw) return [];
            const parsed = JSON.parse(raw);
            return Array.isArray(parsed) ? parsed : [];
        } catch {
            return [];
        }
    }

    _addToRecent(dataUri) {
        const current = this._loadRecent();
        const deduped = current.filter((item) => item !== dataUri);
        const updated = [dataUri, ...deduped].slice(0, 20);
        try {
            localStorage.setItem("info_hub_recent_covers", JSON.stringify(updated));
        } catch {}
        this.state.recentImages = updated;
    }

    async onRecentImageClick(index) {
        if (this.state.applying) return;
        this.state.applying = true;
        try {
            const dataUri = this.state.recentImages[index];
            await this._saveCover(dataUri.split(",")[1]);
            this.props.close();
        } catch {
            this.notification.add(
                _t("Failed to apply the selected image."),
                { type: "danger" }
            );
        } finally {
            this.state.applying = false;
        }
    }

    onToggleUrlPanel() {
        this.state.showUrlPanel = !this.state.showUrlPanel;
        this.state.urlError = "";
        this.state.urlValue = "";
    }

    onUrlInput(ev) {
        this.state.urlValue = ev.target.value;
        this.state.urlError = "";
    }

    async onApplyUrl() {
        const url = this.state.urlValue.trim();
        if (!url) {
            this.state.urlError = _t("Please enter an image URL.");
            return;
        }
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error("Fetch failed");
            const blob = await response.blob();
            const dataUri = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = (e) => resolve(e.target.result);
                reader.onerror = reject;
                reader.readAsDataURL(blob);
            });
            const base64 = dataUri.split(",")[1];
            this._addToRecent(dataUri);
            await this._saveCover(base64);
            this.props.close();
        } catch {
            this.state.urlError = _t("Could not load the image. Please check the URL and try again.");
        } finally {
            this.state.applying = false;
        }
    }

    onUploadClick() {
        this.fileInputRef.el && this.fileInputRef.el.click();
    }

    onFileChange(ev) {
        const file = ev.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = async (e) => {
            const dataUri = e.target.result;
            const base64 = dataUri.split(",")[1];
            try {
                this._addToRecent(dataUri);
                await this._saveCover(base64);
                this.props.close();
            } catch {
                this.notification.add(_t("Failed to save cover image."), { type: "danger" });
            }
        };
        reader.readAsDataURL(file);
    }

    async _urlToBase64(url) {
        const response = await fetch(url);
        if (!response.ok) throw new Error("Fetch failed");
        const blob = await response.blob();
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result.split(",")[1]);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }

    async _saveCover(base64) {
        await this.orm.write("info.hub.article", [this.props.articleId], {
            cover_image: base64,
        });
        this.props.onCoverApplied(base64);
    }

    onDiscard() {
        this.props.close();
    }
}
