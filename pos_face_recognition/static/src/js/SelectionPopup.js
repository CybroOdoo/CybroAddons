import { _t } from "@web/core/l10n/translation";
import { CashierSelectionPopup } from "@pos_hr/app/components/popups/cashier_selection_popup/cashier_selection_popup";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useRef } from "@odoo/owl";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

const MODEL_URL = "/pos_face_recognition/static/src/js/weights";
faceapi.nets.ssdMobilenetv1.loadFromUri(MODEL_URL)
faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL)
faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL)
faceapi.nets.tinyFaceDetector.load(MODEL_URL)
faceapi.nets.faceLandmark68TinyNet.load(MODEL_URL)
faceapi.nets.faceExpressionNet.load(MODEL_URL)
faceapi.nets.ageGenderNet.load(MODEL_URL)
//Patching SelectionPopup component to add face login system
patch(CashierSelectionPopup.prototype, {
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
        this.rootRef = useRef("root");
        this.rootEmp = useRef("rootEmp");
        this.dialog = useService("dialog");
        this.faceMatcher = null;
        this.intervalId = null;
        this.stream = null;
        this.timeoutId = null;
    },
    //    Function which will decide to open the web camera
    async selectEmployee(itemId) {
        this.selectedId = itemId.id;
        this.faceMatcher = null;
        await this.loadImage(itemId)
        if (this.have_image) {
            this.rootRef.el.style.display = "block";
            await this.startWebcam()
        } else {
            this.dialog.add(AlertDialog, {
                title: _t("Authentication failed"),
                body: _t(
                    "Selected cashier have no image.."
                ),
            });
        }
    },

    //    Function which will load the cashier image
    async loadImage(itemId) {
        const user = this.pos.models["hr.employee"].find(
            (emp) => emp.id === itemId.id
        );
        this.have_image = user?.image
        const employee_image = this.rootEmp.el
        if (this.have_image) {
            employee_image.src = "data:image/jpeg;base64," + this.have_image;
            await new Promise((resolve) => {
                employee_image.onload = resolve;
            });

        }
    },
    async startWebcam() {
        const video = document.getElementById('video');
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: false
            });

            video.srcObject = stream;

            await new Promise((resolve) => {
                video.onloadedmetadata = () => {
                    video.play();
                    resolve();
                };
            });

            if (!video.videoWidth || !video.videoHeight) {
                console.error("Video not ready");
                return;
            }

            await this.faceRecognition(video);

        } catch (error) {
            console.error(error);
        }
    },

    //    Function to get the descriptions of cashier image
    async getLabeledFaceDescriptions() {
        const employee_image = this.rootEmp.el;
        const detections = await faceapi
            .detectSingleFace(employee_image)
            .withFaceLandmarks()
            .withFaceExpressions()
            .withFaceDescriptor();
        if (!detections) {
            console.warn("No face detected in employee image.");
            return null;
        }
        return detections
    },

    //    Function which compares the webcam image with cashier image
    async faceRecognition(video) {
        const labeledFaceDescriptors = await this.getLabeledFaceDescriptions();
        if (!labeledFaceDescriptors) return;
        if (!this.faceMatcher) {
            this.faceMatcher = new faceapi.FaceMatcher([labeledFaceDescriptors.descriptor]);
        }
        const canvas = faceapi.createCanvasFromMedia(video);
        document.body.append(canvas);
        const displaySize = {
            width: video.videoWidth,
            height: video.videoHeight
        };
        faceapi.matchDimensions(canvas, displaySize);
        this.intervalId = setInterval(async () => {
            const detections = await faceapi
                .detectAllFaces(video)
                .withFaceLandmarks()
                .withFaceDescriptors();

            for (const detection of detections) {
                const match = this.faceMatcher.findBestMatch(detection.descriptor);
                if (match.distance < 0.4) {
                    clearInterval(this.intervalId);

                    const modal = this.rootRef.el;
                    if (modal) {
                        modal.style.display = 'none';
                        video.srcObject.getTracks().forEach(track => track.stop());
                        canvas.remove();

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
                    }
                    break;
                }
            }
        }, 100);
    },
    willUnmount() {
        if (this.intervalId) clearInterval(this.intervalId);
        if (this.timeoutId) clearTimeout(this.timeoutId);

        if (this.stream) {
            this.stream.getTracks().forEach((track) => track.stop());
        }
    },
})
