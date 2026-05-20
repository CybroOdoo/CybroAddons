/** @odoo-module **/
import { Chatter } from "@mail/chatter/web_portal/chatter";
import { patch } from "@web/core/utils/patch";
import { useRef } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { markEventHandled } from "@web/core/utils/misc";
patch(Chatter.prototype, {
    /**
     * @override
     */
    setup() {
        super.setup();
        this.MyModal = useRef('myModal')
        this.control_menu = useRef('control_menu_dropdown')
    },

    _hideControlMenu() {
        if (this.control_menu?.el) {
            this.control_menu.el.style.display = "none";
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
        if (this.control_menu.el.style.display === "none") {
            this.control_menu.el.style.display = "block";
        }
        else {
            this.control_menu.el.style.display = "none";
        }
    },

    /**
    Download all attachments attached to the record.
    **/
    onClickDownloadAll(ev) {
        var apiUrl = '/web/binary/download_document'; // URL of Odoo controller
        var modelName = this.state.thread.model;
        var tabId = this.state.thread.id;
        fetch(apiUrl + '?param1=' + modelName + '&param2=' + tabId, {
            method: 'GET',
            responseType: 'blob'
        })
            .then(response => response.blob())
            .then(blob => {
                var url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = modelName + '.zip';
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            })
            .catch(error => {
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
        var self = this;
        this._hideControlMenu();
        this._showModalMode("camera");
        const mediaDevices = browser?.navigator?.mediaDevices || window.navigator?.mediaDevices;
        if (!mediaDevices || !mediaDevices.getUserMedia) {
            if (window.isSecureContext === false) {
                alert("Camera access requires a secure context (HTTPS) or localhost. Please open Odoo on https:// or via localhost/127.0.0.1.");
            } else {
                alert("Camera is not available in this browser/context. Please ensure permissions are granted and you're not blocking camera access.");
            }
            return;
        }
        mediaDevices.getUserMedia({
            audio: false,
            video: true
        })
            .then(function (vidStream) {
                // Store stream on instance so ImageCapture can stop it after capturing
                self._cameraStream = vidStream;
                var video = document.getElementById('videoCam');
                if ("srcObject" in video) {
                    video.srcObject = vidStream;
                } else {
                    video.src = window.URL.createObjectURL(vidStream);
                }
                video.onloadedmetadata = function (e) {
                    video.play();
                };
                // Use onclick instead of addEventListener to avoid stacking handlers
                // when the user opens the camera multiple times.
                var stopButton = document.getElementById('stop-camera-button');
                stopButton.onclick = function () {
                    self._stopCamera();
                };
            })
            .catch(function (e) {
                alert(`Error: ${e.name} - ${e.message}`);
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
                pill.innerHTML = `
                    <span class="am-pill-dot"></span>
                    <span class="am-pill-label">Recording…</span>
                    <button class="am-pill-stop" id="am-pill-stop-btn">
                        <i class="fa fa-stop"></i> Stop &amp; Save
                    </button>`;
                document.body.appendChild(pill);
            }
            document.getElementById("am-pill-stop-btn").onclick = () => {
                try {
                    if (mediaRecorder && mediaRecorder.state !== "inactive") {
                        mediaRecorder.stop();
                    }
                } catch (_) { cleanup(); }
            };
        };

        startBtn.onclick = async () => {
            try {
                chunks = [];
                const displayMedia = browser?.navigator?.mediaDevices || window.navigator?.mediaDevices;
                if (!displayMedia || !displayMedia.getDisplayMedia) {
                    if (window.isSecureContext === false) {
                        alert("Screen recording requires a secure context (HTTPS) or localhost.");
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
                    self.state.isAttachmentBoxOpened = true;
                    self.load(self.state.thread, ["attachments"]);
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
        let canvas = document.querySelector("#canvas");
        let video = document.querySelector("#videoCam");
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
        let image_data_url = canvas.toDataURL('image/jpeg');
        var arr = image_data_url.split(','),
            mime = arr[0].match(/:(.*?);/)[1],
            bstr = atob(arr[1]),
            n = bstr.length,
            u8arr = new Uint8Array(n);
        while (n--) {
            u8arr[n] = bstr.charCodeAt(n);
        }
        var f = new File([u8arr], 'image.jpeg', { type: mime });
        // Upload the captured image
        await this.attachmentUploader.uploadFile(f);
        // Stop camera stream and close modal
        this._stopCamera();
        // Open the attachment box and reload attachments so user sees the new file
        this.state.isAttachmentBoxOpened = true;
        this.load(this.state.thread, ["attachments"]);
    },

    /**
Open window to edit image record
**/
    async onClickEditImgRecord(ev) {
        ev.preventDefault();
        markEventHandled(ev, 'AttachmentImage.onClickEditImgRecord');
        var attachment_id = parseInt(ev.target.id);
        await this.env.services.action.doAction({
            name: this.env._t("Attachment"),
            type: 'ir.actions.act_window',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            res_id: attachment_id,
            res_model: 'ir.attachment',
            context: { create: false },
        }, {
            onClose: async () => {
                await location.reload();
            },
        });
    },
});
