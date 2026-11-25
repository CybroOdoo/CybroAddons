/** @odoo-module **/
import kiosk from "@hr_attendance/public_kiosk/public_kiosk_app";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
import { signal, onWillUnmount } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

const MODEL_URL = '/face_recognized_attendance_login/static/src/js/weights';
let modelsLoadedPromise = null;

async function ensureFaceApiLoaded() {
    if (window.faceapi) return;

    await new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = "/face_recognized_attendance_login/static/src/js/face-api.min.js";
        script.onload = () => resolve();
        script.onerror = () => reject(new Error("Failed to load face-api script"));
        document.head.appendChild(script);
    });
}

async function ensureModelsLoaded() {
    if (!modelsLoadedPromise) {
        await ensureFaceApiLoaded();
        const faceapi = window.faceapi;

        modelsLoadedPromise = Promise.all([
            faceapi.nets.ssdMobilenetv1.loadFromUri(MODEL_URL),
            faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
            faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
            faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
        ]).catch((err) => {
            modelsLoadedPromise = null;
            throw err;
        });
    }
    return modelsLoadedPromise;
}

patch(kiosk.kioskAttendanceApp.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.rpc = rpc;
        this.notification = useService("notification");
        this.employee_image = signal.ref("employee_image");
        this.video = signal.ref("video");
        this.state.employee = false;
        this.state.verifiedEmployeeId = null;
        this.isRecognitionActive = false;
        this.currentStream = null;
        this.faceMatcher = null;
        this.faceToken = null;
        this.consecutiveMatchCount = 0;
        this.failedFrameCount = 0;

        onWillUnmount(() => {
            if (this.checkInterval) {
                clearInterval(this.checkInterval);
            }
            this.stopRecognition(document.getElementById('video'));
        });
    },

    async loadImage(employeeId) {
        try {
            const res = await this.rpc("/get_image", {
                employee_id: employeeId,
                token: this.props.token,
            });
            if (!res) {
                this.have_image = false;
                return;
            }

            const imageData = typeof res === "object" ? res.image : res;
            this.faceToken = typeof res === "object" ? res.face_token : null;

            if (!imageData) {
                this.have_image = false;
                return;
            }

            this.have_image = true;
            const employee_image = document.getElementById('employee_image');

            await new Promise((resolve) => {
                employee_image.onload = () => resolve();
                employee_image.onerror = () => {
                    this.have_image = false;
                    resolve();
                };
                employee_image.src = "data:image/png;base64," + imageData;
            });

            this.currentVerificationId = employeeId;
        } catch {
            this.have_image = false;
        }
    },

    async startWebcam() {
        const video = document.getElementById('video');

        try {
            await ensureModelsLoaded();
        } catch {
            this.notification.add(
                _t("Failed to load face recognition system. Please refresh the page."),
                { title: _t("Initialization Error"), type: "danger" }
            );
            return;
        }

        if (!window.isSecureContext) {
            this.notification.add(
                _t("Camera access requires a secure context (HTTPS). Please ensure you are using a secure connection."),
                { title: _t("Security Requirement"), type: "danger" }
            );
            return;
        }

        this.isRecognitionActive = true;
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            if (!this.isRecognitionActive) {
                stream.getTracks().forEach((t) => t.stop());
                return;
            }
            this.currentStream = stream;
            video.srcObject = stream;
            video.style.display = "block";

            // Wait for both metadata and actual video frame readiness
            await new Promise((resolve) => {
                video.onloadedmetadata = () => {
                    video.play().then(() => {
                        const checkReady = setInterval(() => {
                            if (video.videoWidth > 0 && video.videoHeight > 0) {
                                clearInterval(checkReady);
                                resolve();
                            }
                        }, 100);
                    });
                };
            });

            if (video.videoWidth === 0 || video.videoHeight === 0) {
                throw new Error("Video stream width or height is 0");
            }

            await this.faceRecognition(video);
        } catch (error) {
            let message = _t("Your browser does not support camera access or it is disabled. Please check your browser settings.");
            let title = _t("Access Denied!");

            if (error.name === "NotAllowedError" || error.name === "PermissionDeniedError") {
                message = _t("Camera permission was denied. Please allow camera access in your browser settings and try again.");
                title = _t("Permission Denied");
            } else if (error.name === "NotFoundError" || error.name === "DevicesNotFoundError") {
                message = _t("No camera device found. Please ensure a camera is connected and recognized by your system.");
                title = _t("Camera Not Found");
            } else if (error.name === "NotReadableError" || error.name === "TrackStartError") {
                message = _t("The camera is already in use by another application or tab.");
                title = _t("Camera in Use");
            }

            this.notification.add(message, { title: title, type: "danger" });
            this.stopRecognition(video);
        }
    },

    async getLabeledFaceDescriptions() {
        const faceapi = window.faceapi;
        const img = new Image();
        img.crossOrigin = 'anonymous';
        await new Promise((resolve, reject) => {
            img.onload = () => resolve();
            img.onerror = () => reject(new Error("Failed to load employee reference image"));
            img.src = document.getElementById('employee_image').src;
        });

        const detectDescriptor = async (source) => {
            let result = await faceapi
                .detectSingleFace(source, new faceapi.SsdMobilenetv1Options({ minConfidence: 0.2 }))
                .withFaceLandmarks()
                .withFaceDescriptor();

            if (!result) {
                for (const inputSize of [416, 512, 320, 224]) {
                    result = await faceapi
                        .detectSingleFace(source, new faceapi.TinyFaceDetectorOptions({ inputSize, scoreThreshold: 0.2 }))
                        .withFaceLandmarks()
                        .withFaceDescriptor();
                    if (result) break;
                }
            }
            return result;
        };

        const detection = await detectDescriptor(img);
        if (!detection) {
            throw new Error("No face detected in employee reference image");
        }

        const descriptors = [detection.descriptor];

        // Also extract from horizontally flipped image for lighting/angle tolerance
        const flippedCanvas = document.createElement('canvas');
        flippedCanvas.width = img.naturalWidth;
        flippedCanvas.height = img.naturalHeight;
        const ctx = flippedCanvas.getContext('2d');
        if (ctx) {
            ctx.translate(flippedCanvas.width, 0);
            ctx.scale(-1, 1);
            ctx.drawImage(img, 0, 0);
            const flippedDetection = await detectDescriptor(flippedCanvas);
            if (flippedDetection) {
                descriptors.push(flippedDetection.descriptor);
            }
        }

        return new faceapi.LabeledFaceDescriptors('employee', descriptors);
    },

    stopRecognition(video, clearCheckInterval = true) {
        this.isRecognitionActive = false;
        this.isProcessing = false;
        if (this.currentStream) {
            this.currentStream.getTracks().forEach((t) => t.stop());
            this.currentStream = null;
        }
        if (video) {
            video.srcObject = null;
            video.style.display = "none";
        }
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.remove();
            this.canvas = null;
        }
        const modal = document.getElementById("WebCamModal");
        if (modal) modal.style.display = "none";

        this.faceMatcher = null;
        this.consecutiveMatchCount = 0;
        this.failedFrameCount = 0;
        if (clearCheckInterval && this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
    },

    async faceRecognition(video) {
        if (!this.isRecognitionActive) return;

        const faceapi = window.faceapi;
        if (!this.faceMatcher) {
            try {
                const labeledFace = await this.getLabeledFaceDescriptions();
                this.faceMatcher = new faceapi.FaceMatcher([labeledFace]);
            } catch {
                this.notification.add(
                    _t("Failed to initialize face recognition. Please upload a clear image."),
                    { type: "danger", title: _t("Image detection failed!") }
                );
                this.stopRecognition(video);
                return;
            }
        }

        if (video.videoWidth === 0 || video.videoHeight === 0) {
            requestAnimationFrame(() => this.faceRecognition(video));
            return;
        }

        const canvas = faceapi.createCanvasFromMedia(video);
        this.canvas = canvas;
        document.body.append(this.canvas);
        this.canvas.style.display = "none";

        const displaySize = { width: video.videoWidth, height: video.videoHeight };
        faceapi.matchDimensions(this.canvas, displaySize);

        const processFrame = async () => {
            if (!this.isRecognitionActive) return;

            try {
                const detection = await faceapi
                    .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.2 }))
                    .withFaceLandmarks()
                    .withFaceDescriptor();

                if (!detection) {
                    return requestAnimationFrame(processFrame);
                }

                const match = this.faceMatcher.findBestMatch(detection.descriptor);

                // Threshold: 0.45 tolerates natural appearance variations while
                // 8 consecutive matching frames prevents false positives.
                if (match.distance <= 0.45) {
                    this.consecutiveMatchCount++;
                    this.failedFrameCount = 0;

                    if (this.consecutiveMatchCount >= 8) {
                        this.state.employee = true;
                        this.state.verifiedEmployeeId = this.currentVerificationId;
                        this.stopRecognition(video, false);
                        return;
                    }
                } else {
                    this.consecutiveMatchCount = 0;
                    this.failedFrameCount++;
                    if (this.failedFrameCount >= 50) {
                        this.notification.add(_t("Sorry, cannot recognize you"), {
                            title: _t("Recognition Failed!"),
                            type: "danger",
                        });
                        this.stopRecognition(video);
                        return;
                    }
                }

                requestAnimationFrame(processFrame);
            } catch {
                this.stopRecognition(video);
            }
        };

        processFrame();
    },

    async onManualSelection(employeeId, enteredPin) {
        if (this.isProcessing) return;
        this.isProcessing = true;

        this.state.employee = false;
        this.state.verifiedEmployeeId = null;
        this.faceToken = null;

        this.stopRecognition(document.getElementById('video'));

        try {
            await this.loadImage(employeeId);

            if (this.have_image) {
                const modal = document.getElementById("WebCamModal");
                if (modal) modal.style.display = "block";

                await this.startWebcam();

                this.checkInterval = setInterval(() => {
                    if (this.state.employee && this.state.verifiedEmployeeId === employeeId) {
                        clearInterval(this.checkInterval);
                        this.checkInterval = null;

                        this.rpc("/hr_attendance/manual_selection", {
                            token: this.props.token,
                            employee_id: employeeId,
                            pin_code: enteredPin,
                            face_token: this.faceToken,
                        }).then((result) => {
                            if (result?.id || result?.attendance) {
                                this.employeeData = result;
                                this.switchDisplay("greet");
                            } else if (enteredPin) {
                                this.notification.add(_t("Wrong Pin"), { type: "danger" });
                            }
                            this.isProcessing = false;
                        }).catch(() => {
                            this.isProcessing = false;
                        });
                    }
                }, 500);
            } else {
                this.notification.add(_t("Selected employee has no image."), {
                    title: _t("Authentication failed"),
                    type: "danger",
                });
                this.isProcessing = false;
            }
        } catch {
            this.isProcessing = false;
        }
    },

    onCancelRecognition() {
        this.stopRecognition(document.getElementById('video'));
    },
});
