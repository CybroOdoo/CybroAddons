import { _t } from "@web/core/l10n/translation";
import { CashierSelectionPopup } from "@pos_hr/app/components/popups/cashier_selection_popup/cashier_selection_popup";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { signal } from "@odoo/owl";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

let modelsPromise = null;
function loadModels() {
    if (!modelsPromise) {
        const MODEL_URL = "/pos_face_recognition/static/src/js/weights";
        modelsPromise = Promise.all([
            faceapi.nets.ssdMobilenetv1.loadFromUri(MODEL_URL),
            faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
            faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
            faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL),
        ]);
    }
    return modelsPromise;
}

// Patching CashierSelectionPopup component to add face login system
patch(CashierSelectionPopup.prototype, {
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
        this.dialog = useService("dialog");
        this.webCamModalRef = signal.ref();
        this.videoRef = signal.ref();
        this.employeeImageRef = signal.ref();
        this.faceMatcher = null;
        this.intervalId = null;
        this.stream = null;
        this.timeoutId = null;
        this.canvas = null;
    },
    cleanupFaceRecognition() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
            this.timeoutId = null;
        }
        if (this.stream) {
            this.stream.getTracks().forEach((track) => track.stop());
            this.stream = null;
        }
        const video = this.videoRef();
        if (video && video.srcObject) {
            video.srcObject = null;
        }
        if (this.canvas) {
            this.canvas.remove();
            this.canvas = null;
        }
        this.faceMatcher = null;
    },
    cancelFaceRecognition() {
        const modal = this.webCamModalRef();
        if (modal) {
            modal.style.display = "none";
        }
        this.cleanupFaceRecognition();
    },
    handleUnauthorizedLogin(message) {
        this.cancelFaceRecognition();
        this.dialog.add(AlertDialog, {
            title: _t("Unauthorized Login"),
            body: message || _t("Unauthorized login detected! The scanned face does not match the selected cashier."),
        });
    },
    // Function which will decide to open the web camera
    async selectEmployee(itemId) {
        this.cleanupFaceRecognition();
        this.selectedId = itemId.id;
        await this.loadImage(itemId);
        if (this.have_image) {
            const modal = this.webCamModalRef();
            if (modal) {
                modal.style.display = "flex";
            }
            await this.startWebcam();
        } else {
            this.dialog.add(AlertDialog, {
                title: _t("Authentication failed"),
                body: _t("Selected cashier has no image."),
            });
        }
    },

    // Function which will load the cashier image
    async loadImage(itemId) {
        const empId = itemId?.id || itemId;
        let user = itemId;
        if (this.pos?.models?.["hr.employee"]) {
            const empModel = this.pos.models["hr.employee"];
            if (Array.isArray(empModel)) {
                user = empModel.find((emp) => emp.id === empId) || itemId;
            } else if (typeof empModel.get === "function") {
                user = empModel.get(empId) || itemId;
            } else if (typeof empModel.getAll === "function") {
                const allEmps = empModel.getAll();
                user = (Array.isArray(allEmps) ? allEmps.find((emp) => emp.id === empId) : null) || itemId;
            } else if (typeof empModel.search === "function") {
                const searchRes = empModel.search([["id", "=", empId]]);
                user = searchRes?.[0] || itemId;
            }
        }

        const employee_image = this.employeeImageRef();
        if (employee_image) {
            employee_image.crossOrigin = "anonymous";
            let rawImage = user?.image || user?.image_1920 || user?.avatar_512 || itemId?.image || itemId?.image_1920 || itemId?.avatar_512;
            let imageSrc = null;

            if (typeof rawImage === "string" && rawImage.trim().length > 0) {
                imageSrc = rawImage.startsWith("data:") ? rawImage : "data:image/jpeg;base64," + rawImage;
            } else if (empId) {
                imageSrc = `/web/image/hr.employee/${empId}/image`;
            }

            if (imageSrc) {
                this.have_image = true;
                employee_image.src = imageSrc;
                await new Promise((resolve) => {
                    employee_image.onload = () => {
                        if (employee_image.naturalWidth === 0 || employee_image.naturalHeight === 0) {
                            this.have_image = false;
                        }
                        resolve();
                    };
                    employee_image.onerror = () => {
                        this.have_image = false;
                        resolve();
                    };
                });
            } else {
                this.have_image = false;
            }
        } else {
            this.have_image = false;
        }
    },
    async startWebcam() {
        const video = this.videoRef();
        if (!video) return;
        try {
            await loadModels();
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: false
            });
            this.stream = stream;

            video.srcObject = stream;

            await new Promise((resolve) => {
                video.onloadedmetadata = () => {
                    video.play();
                    resolve();
                };
            });

            if (!video.videoWidth || !video.videoHeight) {
                return;
            }

            await this.faceRecognition(video);

        } catch {
            this.cancelFaceRecognition();
            this.dialog.add(AlertDialog, {
                title: _t("Camera Access Failed"),
                body: _t("Unable to access the camera. Please check your camera connection and permissions."),
            });
        }
    },

    // Function to get the descriptions of cashier image
    async getLabeledFaceDescriptions() {
        const employee_image = this.employeeImageRef();
        if (!employee_image) {
            return null;
        }
        const detections = await faceapi
            .detectSingleFace(employee_image)
            .withFaceLandmarks()
            .withFaceExpressions()
            .withFaceDescriptor();
        if (!detections) {
            return null;
        }
        return detections;
    },

    // Function which compares the webcam image with cashier image
    async faceRecognition(video) {
        const labeledFaceDescriptors = await this.getLabeledFaceDescriptions();
        if (!labeledFaceDescriptors || !labeledFaceDescriptors.descriptor) {
            this.cancelFaceRecognition();
            this.dialog.add(AlertDialog, {
                title: _t("Authentication failed"),
                body: _t("Selected cashier has no valid face image."),
            });
            return;
        }
        
        this.faceMatcher = new faceapi.FaceMatcher([labeledFaceDescriptors.descriptor]);

        const canvas = faceapi.createCanvasFromMedia(video);
        this.canvas = canvas;
        document.body.append(canvas);
        const displaySize = {
            width: video.videoWidth,
            height: video.videoHeight
        };
        faceapi.matchDimensions(canvas, displaySize);

        // Timeout to abort matching and warn if no face matches within 10s
        this.timeoutId = setTimeout(() => {
            this.handleUnauthorizedLogin(
                _t("Face recognition timed out. No matching face detected.")
            );
        }, 10000);

        let nonMatchCount = 0;
        let isProcessing = false;

        this.intervalId = setInterval(async () => {
            if (!this.faceMatcher || !video || isProcessing) return;
            isProcessing = true;

            try {
                const detections = await faceapi
                    .detectAllFaces(video)
                    .withFaceLandmarks()
                    .withFaceDescriptors();

                if (!this.faceMatcher) return;

                let matchFound = false;
                for (const detection of detections) {
                    const match = this.faceMatcher?.findBestMatch(detection.descriptor);
                    if (match && match.distance < 0.4) {
                        matchFound = true;
                        this.cancelFaceRecognition();

                        const employee = this.pos.models["hr.employee"].find(
                            (emp) => emp.id === this.selectedId
                        );
                        if (employee) {
                            // Bypass PIN check: return a Proxy that hides the _pin from the caller
                            const proxyEmployee = new Proxy(employee, {
                                get(target, key) {
                                    if (key === "_pin") {
                                        return null;
                                    }
                                    const value = target[key];
                                    return typeof value === "function" ? value.bind(target) : value;
                                },
                            });
                            this.props.getPayload(proxyEmployee);
                            this.props.close();
                        }
                        break;
                    }
                }

                if (!matchFound && detections.length > 0) {
                    nonMatchCount++;
                    // If a non-matching face is continuously seen, raise unauthorized warning
                    if (nonMatchCount >= 10) {
                        this.handleUnauthorizedLogin(
                            _t("Unauthorized login detected! The detected face does not match the selected cashier.")
                        );
                    }
                }
            } catch {
                // Ignore transient detection errors during video frame processing
            } finally {
                isProcessing = false;
            }
        }, 100);
    },
    willUnmount() {
        this.cleanupFaceRecognition();
        super.willUnmount?.();
    },
});
