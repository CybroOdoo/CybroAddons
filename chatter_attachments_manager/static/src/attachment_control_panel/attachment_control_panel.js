/** @odoo-module **/
import { Chatter } from "@mail/chatter/web_portal_project/chatter";
import { patch } from "@web/core/utils/patch";
import { onWillUnmount, signal } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { markEventHandled } from "@web/core/utils/misc";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

function makeRef() {
    const r = signal.ref();
    Object.defineProperty(r, "el", {
        get() {
            return r();
        },
    });
    return r;
}

patch(Chatter.prototype, {
    /**
     * @override
     */
    setup() {
        super.setup();
        this.notification = useService("notification");
        this.MyModal = makeRef();
        this.control_menu = makeRef();
        this._onAmDocClick = (ev) => {
            if (!ev.target.closest(".am-upload-wrapper")) {
                this._hideControlMenu();
            }
        };
        document.addEventListener("click", this._onAmDocClick);
        onWillUnmount(() => {
            document.removeEventListener("click", this._onAmDocClick);
            this._stopCamera();
        });
    },

    notify(message, type = "warning") {
        if (this.notification) {
            this.notification.add(message, { type });
        } else if (this.env.services?.notification) {
            this.env.services.notification.add(message, { type });
        }
    },

    _hideControlMenu() {
        const el = this.control_menu?.();
        if (el) {
            el.style.display = "none";
        }
    },

    _showModalMode(mode) {
        if (!this.MyModal?.el) {
            return;
        }
        this.MyModal.el.style.display = "flex";
        const capture = document.getElementById("capture");
        const screenContainer = document.getElementById("screen_recording_container");
        const video = document.getElementById("videoCam");
        if (mode === "camera") {
            if (screenContainer) {
                screenContainer.style.display = "none";
            }
            if (capture) {
                capture.style.display = "block";
            }
            if (video) {
                video.style.display = "block";
            }
        } else if (mode === "screen") {
            if (screenContainer) {
                screenContainer.style.display = "block";
            }
            if (capture) {
                capture.style.display = "none";
            }
            if (video) {
                video.style.display = "none";
            }
        }
    },
    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
      Open a dropdown on click upload icon
    **/
    onClickUpload(ev) {
        const el = this.control_menu?.();
        if (!el) {
            return;
        }
        if (el.style.display === "none") {
            el.style.display = "block";
        } else {
            el.style.display = "none";
        }
    },

    /**
    Download all attachments attached to the record.
    **/
    onClickDownloadAll(ev) {
        const modelName = this.state.thread?.model;
        const tabId = this.state.thread?.id;
        if (!modelName || !tabId) {
            return;
        }
        const attachments = this.attachments || this.state.thread?.attachments;
        if (Array.isArray(attachments) && attachments.length === 0) {
            this.notify(_t("No attachments found to download."));
            return;
        }
        const apiUrl = '/chatter_attachments_manager/download_document';
        fetch(apiUrl + '?param1=' + encodeURIComponent(modelName) + '&param2=' + encodeURIComponent(tabId), {
            method: 'GET',
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Download failed with status " + response.status);
                }
                return response.blob();
            })
            .then((blob) => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = modelName + '.zip';
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            })
            .catch(() => {
                this.notify(_t("Could not download attachments. Please ensure attachments exist and are accessible."), "danger");
            });
    },

    /**
       Open camera to capture
    **/
    /**
     * Stop the active camera stream and close the camera modal.
     */
    _stopCamera() {
        if (this._cameraStream) {
            this._cameraStream.getTracks().forEach(function (track) {
                track.stop();
            });
            this._cameraStream = null;
        }
        if (this.MyModal?.el) {
            this.MyModal.el.style.display = "none";
        }
    },

    onClickCamera(ev) {
        const self = this;
        this._hideControlMenu();
        this._showModalMode("camera");
        const mediaDevices = browser?.navigator?.mediaDevices || window.navigator?.mediaDevices;
        if (!mediaDevices || !mediaDevices.getUserMedia) {
            if (window.isSecureContext === false) {
                this.notify(_t("Camera access requires a secure context (HTTPS) or localhost. Please open Odoo on https:// or via localhost/127.0.0.1."));
            } else {
                this.notify(_t("Camera is not available in this browser/context. Please ensure permissions are granted and you're not blocking camera access."));
            }
            return;
        }
        mediaDevices.getUserMedia({
            audio: false,
            video: true,
        })
            .then((vidStream) => {
                self._cameraStream = vidStream;
                const video = document.getElementById('videoCam');
                if (video) {
                    video.srcObject = vidStream;
                    video.onloadedmetadata = () => {
                        video.play();
                    };
                }
                const stopButton = document.getElementById('stop-camera-button');
                if (stopButton) {
                    stopButton.onclick = () => {
                        self._stopCamera();
                    };
                }
            })
            .catch((e) => {
                this.notify(_t("Unable to access camera: %(error)s", { error: e ? e.message : "" }), "danger");
            });
    },
    /**
      Record the screen.
    **/
    async onClickScreenRec(ev) {
        this._hideControlMenu();
        this._showModalMode("screen");

        const startBtn = document.getElementById("start_record_button");
        const stopBtn = document.getElementById("stop_record_button");

        if (!startBtn || !stopBtn) {
            return;
        }

        // Reset button states every time the modal opens
        startBtn.style.display = "";
        stopBtn.style.display = "none";

        let stream;
        let mediaRecorder;
        let chunks = [];
        const self = this;

        /** Remove all tracks and reset state */
        const cleanup = () => {
            if (stream) {
                stream.getTracks().forEach((t) => t.stop());
            }
            stream = undefined;
            mediaRecorder = undefined;
            chunks = [];
            // Remove floating recording pill
            const pill = document.getElementById("am-recording-pill");
            if (pill) { pill.remove(); }
        };

        /** Close the modal and show a floating pill so recording can continue */
        const showRecordingPill = () => {
            if (self.MyModal?.el) {
                self.MyModal.el.style.display = "none";
            }
            let pill = document.getElementById("am-recording-pill");
            if (!pill) {
                pill = document.createElement("div");
                pill.id = "am-recording-pill";
                const dot = document.createElement("span");
                dot.className = "am-pill-dot";
                const label = document.createElement("span");
                label.className = "am-pill-label";
                label.textContent = _t("Recording…");
                const stopBtnEl = document.createElement("button");
                stopBtnEl.className = "am-pill-stop";
                stopBtnEl.id = "am-pill-stop-btn";
                const icon = document.createElement("i");
                icon.className = "fa fa-stop me-1";
                stopBtnEl.appendChild(icon);
                stopBtnEl.appendChild(document.createTextNode(" " + _t("Stop & Save")));
                pill.appendChild(dot);
                pill.appendChild(label);
                pill.appendChild(stopBtnEl);
                document.body.appendChild(pill);
            }
            const stopBtnEl = document.getElementById("am-pill-stop-btn");
            if (stopBtnEl) {
                stopBtnEl.onclick = () => {
                    try {
                        if (mediaRecorder && mediaRecorder.state !== "inactive") {
                            mediaRecorder.stop();
                        }
                    } catch (_) { cleanup(); }
                };
            }
        };

        startBtn.onclick = async () => {
            try {
                chunks = [];
                const displayMedia = browser?.navigator?.mediaDevices || window.navigator?.mediaDevices;
                if (!displayMedia || !displayMedia.getDisplayMedia) {
                    if (window.isSecureContext === false) {
                        self.notify(_t("Screen recording requires a secure context (HTTPS) or localhost."));
                    }
                    return;
                }
                stream = await displayMedia.getDisplayMedia({ video: true, audio: true });
                const mime = MediaRecorder.isTypeSupported("video/webm; codecs=vp9")
                    ? "video/webm; codecs=vp9"
                    : "video/webm";
                mediaRecorder = new MediaRecorder(stream, { mimeType: mime });

                mediaRecorder.addEventListener("dataavailable", (e) => {
                    if (e.data && e.data.size) { chunks.push(e.data); }
                });

                mediaRecorder.addEventListener("stop", async () => {
                    // Snapshot chunks BEFORE cleanup() resets the array
                    const recordedChunks = [...chunks];
                    cleanup();
                    if (!recordedChunks.length) { return; }
                    const blob = new Blob(recordedChunks, { type: recordedChunks[0]?.type || "video/webm" });
                    const file = new File([blob], "screen_record.webm", { type: blob.type });
                    // Upload and refresh attachment box without a full page reload
                    await self.attachmentUploader.uploadFile(file);
                    if (self.hasParentReloadOnAttachmentsChanged) {
                        self.reloadParentView();
                    }
                    if (self.CHATTER_PANEL) {
                        self.state.activePanel = self.CHATTER_PANEL.ATTACHMENT;
                    }
                });

                mediaRecorder.start();
                // Update button visibility
                startBtn.style.display = "none";
                stopBtn.style.display = "";
                // Close modal, show floating pill
                showRecordingPill();

                // Handle browser-native "Stop sharing" button
                stream.getVideoTracks()[0]?.addEventListener("ended", () => {
                    try {
                        if (mediaRecorder && mediaRecorder.state !== "inactive") {
                            mediaRecorder.stop();
                        }
                    } catch (_) { }
                });

            } catch (e) {
                cleanup();
            }
        };

        stopBtn.onclick = () => {
            try {
                if (mediaRecorder && mediaRecorder.state !== "inactive") {
                    mediaRecorder.stop();
                }
            } catch (e) {
                cleanup();
            }
        };
    },

    /**
     Capture the image from the live webcam feed, upload it,
     stop the camera stream, and refresh the attachment box.
    **/
    async ImageCapture() {
        const canvas = document.querySelector("#canvas");
        const video = document.querySelector("#videoCam");
        if (!canvas || !video) {
            return;
        }
        canvas.width = video.videoWidth || 1280;
        canvas.height = video.videoHeight || 720;
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
        const image_data_url = canvas.toDataURL('image/jpeg');
        const arr = image_data_url.split(',');
        const mime = arr[0].match(/:(.*?);/)[1];
        const bstr = atob(arr[1]);
        let n = bstr.length;
        const u8arr = new Uint8Array(n);
        while (n--) {
            u8arr[n] = bstr.charCodeAt(n);
        }
        const f = new File([u8arr], `capture_${Date.now()}.jpeg`, { type: mime });
        // Upload the captured image
        await this.attachmentUploader.uploadFile(f);
        // Stop camera stream and close modal
        this._stopCamera();
        // Open the attachment box and reload attachments so user sees the new file
        if (this.hasParentReloadOnAttachmentsChanged) {
            this.reloadParentView();
        }
        if (this.CHATTER_PANEL) {
            this.state.activePanel = this.CHATTER_PANEL.ATTACHMENT;
        }
    },

    /**
     * Open window to edit image record
     */
    async onClickEditImgRecord(ev) {
        ev.preventDefault();
        markEventHandled(ev, 'AttachmentImage.onClickEditImgRecord');
        const attachment_id = parseInt(ev.target.id, 10);
        const self = this;
        await this.env.services.action.doAction({
            name: _t("Attachment"),
            type: 'ir.actions.act_window',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            res_id: attachment_id,
            res_model: 'ir.attachment',
            context: { create: false },
        }, {
            onClose: async () => {
                try {
                    const orm = self.orm || self.env.services?.orm;
                    const store = self.store || self.env.services?.["mail.store"];
                    if (orm && attachment_id) {
                        const attachmentsData = await orm.read(
                            "ir.attachment",
                            [attachment_id],
                            [
                                "name",
                                "mimetype",
                                "file_size",
                                "checksum",
                                "res_model",
                                "res_id",
                                "access_token",
                                "description",
                            ],
                            { load: false }
                        );
                        if (attachmentsData && attachmentsData.length > 0) {
                            const updated = attachmentsData[0];
                            const updateVals = {
                                id: attachment_id,
                                name: updated.name,
                                mimetype: updated.mimetype,
                                file_size: updated.file_size,
                                checksum: updated.checksum,
                                extension: updated.name ? updated.name.split(".").pop().toLowerCase() : "",
                            };
                            if (updated.access_token) {
                                updateVals.access_token = updated.access_token;
                            }
                            if (store) {
                                store.insert({ "ir.attachment": updateVals });
                            }
                            const att = store?.["ir.attachment"]?.get(attachment_id);
                            if (att) {
                                if (typeof att.update === "function") {
                                    att.update(updateVals);
                                }
                                att.name = updated.name;
                                if (updated.name) {
                                    att.extension = updated.name.split(".").pop().toLowerCase();
                                }
                                if (updated.checksum) {
                                    att.checksum = updated.checksum;
                                }
                                if (updated.mimetype) {
                                    att.mimetype = updated.mimetype;
                                }
                                if (updated.file_size !== undefined && updated.file_size !== false) {
                                    att.file_size = updated.file_size;
                                }
                                if (updated.access_token) {
                                    att.access_token = updated.access_token;
                                }
                            }
                            const imgSelector = `img[src*="/web/image/${attachment_id}"], img[src*="/web/content/${attachment_id}"]`;
                            document.querySelectorAll(imgSelector).forEach((img) => {
                                const baseSrc = img.src.split('?')[0];
                                img.src = `${baseSrc}?unique=${encodeURIComponent(updated.checksum || Date.now())}&t=${Date.now()}`;
                            });
                        } else {
                            store?.["ir.attachment"]?.get(attachment_id)?.delete?.();
                        }
                    }
                } catch {
                    // Suppress refresh errors gracefully
                }

                if (typeof self.render === "function") {
                    self.render();
                }
                if (self.hasParentReloadOnAttachmentsChanged) {
                    self.reloadParentView();
                }
                if (self.state.thread?.fetchNewMessages) {
                    await self.state.thread.fetchNewMessages();
                }
            },
        });
    },
});
