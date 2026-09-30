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
        this.isRecognitionActive = false;
        this.currentStream = null;
        this.faceMatcher = null;
        this.recognitionResolve = null;

        onWillUnmount(() => {
            this.stopRecognition(this.video.el, false);
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

    stopRecognition(video, resultValue = false) {
        this.isRecognitionActive = false;

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

        if (this.recognitionResolve) {
            const resolve = this.recognitionResolve;
            this.recognitionResolve = null;
            resolve(resultValue);
        }
    },

    async startWebcam() {
        const video = this.video.el;
        if (video) {
            video.style.display = 'block';
        }

        try {
            await ensureModelsLoaded();
        } catch (error) {
            console.error("Failed to load face-api:", error);
            this.notification.add(
                _t("Failed to load face recognition system. Please refresh the page."),
                { title: "Initialization Error", type: "danger" }
            );
            return false;
        }

        if (!window.isSecureContext) {
            console.error("Camera access requires a secure context (HTTPS).");
            this.notification.add(
                _t("Camera access requires a secure context (HTTPS). Please ensure you are using a secure connection."),
                { title: "Security Requirement", type: "danger" }
            );
            return false;
        }

        this.isRecognitionActive = true;
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            if (!this.isRecognitionActive) {
                stream.getTracks().forEach((t) => t.stop());
                return false;
            }
            this.currentStream = stream;
            video.srcObject = stream;

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
                throw new Error("Video not ready — width or height is 0");
            }

            return await this.runFaceRecognition(video);
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
            this.stopRecognition(video, false);
            return false;
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

        return new faceapi.LabeledFaceDescriptors("employee", [detections.descriptor]);
    },

    runFaceRecognition(video) {
        return new Promise(async (resolve) => {
            this.recognitionResolve = resolve;

            try {
                const labeledFace = await this.getLabeledFaceDescriptions();
                // Threshold set to 0.50 for reliable matching
                this.faceMatcher = new faceapi.FaceMatcher([labeledFace], 0.50);
            } catch (err) {
                console.error("Could not get face descriptor from profile image:", err);
                this.notification.add(
                    _t("No face detected in employee profile picture. Please upload a clear face image."),
                    { type: "danger", title: _t("Recognition Failed!") }
                );
                this.stopRecognition(video, false);
                return;
            }

            const canvas = faceapi.createCanvasFromMedia(video);
            this.canvas = canvas;
            document.body.append(this.canvas);
            this.canvas.style.display = "none";

            const displaySize = { width: video.videoWidth, height: video.videoHeight };
            faceapi.matchDimensions(this.canvas, displaySize);

            let consecutiveMatches = 0;
            let noMatchCount = 0;
            let emptyFrameCount = 0;

            const processFrame = async () => {
                if (!this.isRecognitionActive) return;

                try {
                    const detections = await faceapi
                        .detectAllFaces(video)
                        .withFaceLandmarks()
                        .withFaceDescriptors();

                    if (detections.length === 0) {
                        consecutiveMatches = 0;
                        emptyFrameCount++;
                        if (emptyFrameCount >= 150) { // ~8-10 seconds of no face in frame
                            this.notification.add(
                                _t("No face detected in camera view. Recognition timed out."),
                                { title: _t("Recognition Failed!"), type: "danger" }
                            );
                            this.stopRecognition(video, false);
                            return;
                        }
                        return requestAnimationFrame(processFrame);
                    }

                    emptyFrameCount = 0;
                    let matchFound = false;

                    for (const detection of detections) {
                        const match = this.faceMatcher.findBestMatch(detection.descriptor);

                        if (match.label === "employee" && match.distance <= 0.50) {
                            matchFound = true;
                            consecutiveMatches++;
                            if (consecutiveMatches >= 2) {
                                this.stopRecognition(video, true);
                                return;
                            }
                            break;
                        }
                    }

                    if (!matchFound) {
                        consecutiveMatches = 0;
                        noMatchCount++;
                        if (noMatchCount >= 20) { // ~1.5 - 2 seconds of scanning non-matching face
                            this.notification.add(
                                _t("Face recognition failed. Face does not match the selected employee."),
                                { title: _t("Recognition Failed!"), type: "danger" }
                            );
                            this.stopRecognition(video, false);
                            return;
                        }
                    }

                    requestAnimationFrame(processFrame);
                } catch (error) {
                    console.error("Face recognition error:", error);
                    this.stopRecognition(video, false);
                }
            };

            processFrame();
        });
    },

    async onManualSelection(employeeId, enteredPin) {
        if (this.isProcessing) return;
        this.isProcessing = true;

        this.stopRecognition(this.video.el, false);

        try {
            await this.loadImage(employeeId);

            if (this.have_image) {
                const modal = document.getElementById("WebCamModal");
                if (modal) modal.style.display = "block";

                const isVerified = await this.startWebcam();

                if (isVerified) {
                    const route = '/hr_attendance/manual_selection';
                    const params = {
                        token: this.props.token,
                        employee_id: employeeId,
                        pin_code: enteredPin,
                    };
                    const result = typeof this.makeRpcWithGeolocation === 'function'
                        ? await this.makeRpcWithGeolocation(route, params)
                        : await this.rpc(route, params);

                    if (result?.id || result?.attendance || result?.employee_name) {
                        this.employeeData = result;
                        this.switchDisplay("greet");
                    } else if (enteredPin) {
                        this.notification.add(_t("Wrong Pin"), { type: "danger" });
                    }
                }
            } else {
                this.notification.add(_t("Selected employee has no image."), {
                    title: _t("Authentication failed"),
                    type: "danger",
                });
            }
        } catch (error) {
            console.error("Error during manual selection:", error);
        } finally {
            this.isProcessing = false;
        }
    },

    onCancelRecognition() {
        this.stopRecognition(this.video.el, false);
        this.isProcessing = false;
    },
});