/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { LoginScreen } from "@pos_hr/app/login_screen/login_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useRef, useState } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
//Loading faceapi weights
const MODEL_URL = '/pos_face_recognition/static/src/js/weights';
faceapi.nets.ssdMobilenetv1.loadFromUri(MODEL_URL)
faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL)
faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL)
faceapi.nets.tinyFaceDetector.load(MODEL_URL),
faceapi.nets.faceLandmark68TinyNet.load(MODEL_URL),
faceapi.nets.faceExpressionNet.load(MODEL_URL),
faceapi.nets.ageGenderNet.load(MODEL_URL)

//Patching LoginScreen component to add face login system
patch(LoginScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.state = useState({
            imageUrl: false
        })
        this.orm = useService("orm");
        this.root = useRef("LoginRoot");
        this.popup = useService("popup");
        this.faceMatcher = null;
    },
//    Function which will decide to open the web camera
    async back() {
        await this.loadImage()
        if (this.have_image != false) {
            await this.startWebcam()
        } else {
            await this.popup.add(ErrorPopup, {
                title: _t("Authentication failed"),
                body: _t("Selected cashier have no image.."),
            });
            location.reload();
        }
    },

//    Function which will load the cashier image
    async loadImage(){
        var user = await this.orm.searchRead("hr.employee", [['id', '=', this.pos.cashier.id]], ['image']);
        this.have_image = user[0].image
        const employee_image = this.root.el.querySelector('#employee_image')
        if (this.have_image != false) {
            employee_image.src = "data:image/jpeg;base64," + user[0].image
        }
    },

//    Function to start the web camera
    startWebcam(){
        const video = this.root.el.querySelector('#video')
        navigator.mediaDevices.getUserMedia(
        { video: true, audio: false }
        ).then((stream) => {
            video.srcObject = stream
        }).catch((error) => {
            console.error(error)
        }).then(this.faceRecognition(video))
    },

//    Function to get the descriptions of cashier image
    async getLabeledFaceDescriptions(){
        const employee_image = this.root.el.querySelector('#employee_image');
        const detections = await faceapi
                    .detectSingleFace(employee_image)
                    .withFaceLandmarks()
                    .withFaceExpressions()
                    .withFaceDescriptor();
        return detections
    },

//    Function which compares the webcam image with cashier image
    async faceRecognition(video){
        const labeledFaceDescriptors = await this.getLabeledFaceDescriptions()
        if (!this.faceMatcher) {
            this.faceMatcher = new faceapi.FaceMatcher([labeledFaceDescriptors.descriptor]);
        }
        video.addEventListener('play', () => {
            const canvas = faceapi.createCanvasFromMedia(video);
            document.body.append(canvas);
            const displaySize = {width: video.width, height: video.height}
            faceapi.matchDimensions(canvas, displaySize)
            setInterval(async () => {
                const detections = await faceapi
                    .detectAllFaces(video)
                    .withFaceLandmarks()
                    .withFaceExpressions()
                    .withFaceDescriptors();
                    detections.forEach((detection) => {
                    const match = this.faceMatcher.findBestMatch(detection.descriptor);
                    if (match._distance < 0.4  ) { // Adjust threshold as needed
                        const modal = document.getElementById('WebCamModal');
                        if (modal) {
                            modal.style.display = 'none';
                            this.modalVisible = false;
                            this.props.resolve({ confirmed: false, payload: false });
                            this.pos.closeTempScreen();
                            this.pos.hasLoggedIn = true;
                            this.pos.openCashControl();
                            video.srcObject.getTracks().forEach(track => track.stop());
                            canvas.remove();
                        }
                    }
                });
            }, 100);
        })
    },
})