/** @odoo-module **/
import kiosk from "@hr_attendance/public_kiosk/public_kiosk_app";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
import { useRef, onWillUnmount } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

const MODEL_URL = '/face_recognized_attendance_login/static/src/js/weights';
let modelsLoadedPromise = null;

async function ensureFaceApiLoaded() {
    if (window.faceapi) return;

    await new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = "/face_recognized_attendance_login/static/src/js/face-api.min.js";
        script.onload = () => resolve();
        script.onerror = (err) => reject(err);
        document.head.appendChild(script);
    });
}

async function ensureModelsLoaded() {
    if (!modelsLoadedPromise) {
        await ensureFaceApiLoaded();

        modelsLoadedPromise = Promise.all([
            faceapi.nets.ssdMobilenetv1.loadFromUri(MODEL_URL),
            faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
            faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
            faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
            faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL),
        ]).catch((err) => {
            console.error("Error loading face-api models:", err);
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
        this.employee_image = useRef("employee_image");
        this.video = useRef("video");
        this.state.employee = false;
        this.state.verifiedEmployeeId = null;
        this.isRecognitionActive = false;
        this.currentStream = null;
        this.faceMatcher = null;
        this.noMatchCount = 0;

        onWillUnmount(() => {
            if (this.checkInterval) {
                clearInterval(this.checkInterval);
            }
            this.stopRecognition(this.video.el);
        });
    },

    async loadImage(employeeId) {
        try {
            const image = await this.rpc("/get_image", { employee_id: employeeId });
            if (!image) {
                this.have_image = false;
                return;
            }

            this.have_image = true;
            const employee_image = this.employee_image.el;

            await new Promise((resolve) => {
                employee_image.onload = () => resolve();
                employee_image.onerror = () => {
                    this.have_image = false;
                    resolve();
                };
                employee_image.src = "data:image/jpeg;base64," + image;
            });

            this.currentVerificationId = employeeId;
        } catch (error) {
            console.error("Failed to load image:", error);
            this.have_image = false;
        }
    },

     async startWebcam() {
        const video = this.video.el;

        try {
            await ensureModelsLoaded();
        } catch (error) {
            console.error("Failed to load face-api:", error);
            this.notification.add(
                _t("Failed to load face recognition system. Please refresh the page."),
                { title: "Initialization Error", type: "danger" }
            );
            return;
        }

        if (!window.isSecureContext) {
            console.error("Camera access requires a secure context (HTTPS).");
            this.notification.add(
                _t("Camera access requires a secure context (HTTPS). Please ensure you are using a secure connection."),
                { title: "Security Requirement", type: "danger" }
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

            // Ensure non-zero dimensions before recognition
            if (video.videoWidth === 0 || video.videoHeight === 0) {
                throw new Error("Video not ready — width or height is 0");
            }

            await this.faceRecognition(video);
        } catch (error) {
            console.error("Error starting webcam:", error);
            let message = _t("Your browser does not support camera access or it is disabled. Please check your browser settings.");
            let title = "Access Denied!";

            if (error.name === "NotAllowedError" || error.name === "PermissionDeniedError") {
                message = _t("Camera permission was denied. Please allow camera access in your browser settings and try again.");
                title = "Permission Denied";
            } else if (error.name === "NotFoundError" || error.name === "DevicesNotFoundError") {
                message = _t("No camera device found. Please ensure a camera is connected and recognized by your system.");
                title = "Camera Not Found";
            } else if (error.name === "NotReadableError" || error.name === "TrackStartError") {
                message = _t("The camera is already in use by another application or tab.");
                title = "Camera in Use";
            }

            this.notification.add(message, { title: title, type: "danger" });
            this.stopRecognition(video);
        }
    },

    async getLabeledFaceDescriptions() {
        const img = new Image();
        await new Promise((resolve, reject) => {
            img.onload = () => resolve();
            img.onerror = (e) => reject(e);
            img.src = this.employee_image.el.src;
        });
        
        let detections = await faceapi
            .detectSingleFace(img)
            .withFaceLandmarks()
            .withFaceDescriptor();

        if (!detections) {
            detections = await faceapi
                .detectSingleFace(img, new faceapi.TinyFaceDetectorOptions())
                .withFaceLandmarks()
                .withFaceDescriptor();
        }

        if (!detections) {
            throw new Error("No face detected in employee image");
        }

        return detections;
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
        this.noMatchCount = 0;
        if (clearCheckInterval && this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
    },

    async faceRecognition(video) {
        if (!this.isRecognitionActive) return;

        if (!this.faceMatcher) {
            try {
                const labeledFace = await this.getLabeledFaceDescriptions();
                this.faceMatcher = new faceapi.FaceMatcher([labeledFace.descriptor]);
            } catch (err) {
                console.error("Could not get face descriptor:", err);
                this.notification.add(
                    _t("Failed to initialize face recognition. Please upload a clear image."),
                    { type: "danger", title: "Image detection failed!" }
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
                const detections = await faceapi
                    .detectAllFaces(video)
                    .withFaceLandmarks()
                    .withFaceDescriptors();

                if (detections.length === 0) {
                    return requestAnimationFrame(processFrame);
                }

                for (const detection of detections) {
                    const match = this.faceMatcher.findBestMatch(detection.descriptor);
                    
                    if (match.distance <= 0.55) {
                        this.state.employee = true;
                        this.state.verifiedEmployeeId = this.currentVerificationId;
                        this.stopRecognition(video, false);
                        return;
                    } else {
                        this.noMatchCount++;
                        if (this.noMatchCount >= 50) {
                            this.notification.add(_t("Sorry, cannot recognize you"), {
                                title: "Recognition Failed!",
                                type: "danger",
                            });
                            this.stopRecognition(video);
                            return;
                        }
                    }
                }

                requestAnimationFrame(processFrame);
            } catch (error) {
                console.error("Face recognition error:", error);
                this.stopRecognition(video);
            }
        };

        processFrame();
    },

    async onManualSelection(employeeId, enteredPin) {
        if (this.isProcessing) return;
        this.isProcessing = true;
        this.stopRecognition(this.video.el);

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
                        }).then((result) => {
                            if (result?.id || result?.attendance) {
                                this.employeeData = result;
                                this.switchDisplay("greet");
                            } else if (enteredPin) {
                                this.notification.add(_t("Wrong Pin"), { type: "danger" });
                            }
                            this.isProcessing = false;
                        }).catch((error) => {
                            console.error("Manual selection RPC failed:", error);
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
        } catch (error) {
            console.error("Error during manual selection:", error);
            this.isProcessing = false;
        }
    },

    onCancelRecognition() {
        this.stopRecognition(this.video.el);
    },
});
