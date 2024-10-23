/** @odoo-module **/

const LoginScreen = require('pos_hr.LoginScreen');
import { patch } from "@web/core/utils/patch";
const {_t} = require('web.core');
const {useService} = require("@web/core/utils/hooks");
import { onMounted, useRef, useState } from "@odoo/owl";
var ajax = require('web.ajax');
const {Gui} = require('point_of_sale.Gui');
const {posbus} = require('point_of_sale.utils');
const MODEL_URL = '/pos_face_recognition/static/src/js/weights';
faceapi.nets.ssdMobilenetv1.loadFromUri(MODEL_URL)
faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL)
faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL)
faceapi.nets.tinyFaceDetector.load(MODEL_URL),
faceapi.nets.faceLandmark68TinyNet.load(MODEL_URL),
faceapi.nets.faceExpressionNet.load(MODEL_URL),
faceapi.nets.ageGenderNet.load(MODEL_URL)

// patching Login Screen
patch(LoginScreen.prototype, 'pos_hr/static/src/js/LoginScreen.js', {
    // setup function
    setup() {
        this._super.apply(this, arguments);
        this.root = useRef("LoginRoot");
        this.ImageRoot = useRef("ImageRoot");
        this.faceMatcher = null;
    },

    // overriding back function
    async back() {
        await this.loadImage()
    },

    // Function to loadimage
    async loadImage() {
        var cashier_id = this.env.pos.get_cashier().id
        await ajax.jsonRpc('/cashier/image/', 'call', {
            cashier_id: cashier_id,
        }).then(async data => {
            if (data) {
                this.have_image = data
                const employee_image = this.ImageRoot.el;
                employee_image.src = "data:image/jpeg;base64," + data
                await this.startWebcam()
            } else {
                await Gui.showPopup("ErrorPopup", {
                    'title': _t('Authentication failed'),
                    'body': _t('Selected cashier have no image..'),
                });
                location.reload();
            }
        });
    },

    // Function to start webcam
    startWebcam() {
        const video = this.root.el.querySelector('#video')
        navigator.mediaDevices.getUserMedia(
            {video: true, audio: false}
        ).then((stream) => {
            video.srcObject = stream
        }).catch((error) => {
            console.error(error)
        }).then(this.faceRecognition(video))
    },

    //    Function to get the descriptions of cashier image
    async getLabeledFaceDescriptions() {
        const employee_image = this.ImageRoot.el;
        const detections = await faceapi
            .detectSingleFace(employee_image)
            .withFaceLandmarks()
            .withFaceExpressions()
            .withFaceDescriptor();
        return detections
    },
    //    Function which compares the webcam image with cashier image
    async faceRecognition(video) {
        const labeledFaceDescriptors = await this.getLabeledFaceDescriptions()
        if (!this.faceMatcher) {
            this.faceMatcher = new faceapi.FaceMatcher([labeledFaceDescriptors.descriptor]);
        }
        this.root.el.querySelector('.screen-login').style.zIndex = -1
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
                    if (match._distance < 0.4) { // Adjust threshold as needed
                        const modal = this.root.el.querySelector('#WebCamModal');
                        if (modal) {
                            modal.style.display = 'none';
                            this.props.resolve({
                                confirmed: false,
                                payload: false
                            });
                            this.trigger('close-temp-screen');
                            this.env.pos.hasLoggedIn = true;
                            this.env.posbus.trigger('start-cash-control');
                            video.srcObject.getTracks().forEach(track => track.stop());
                            canvas.remove();
                        }
                    } else {
                        Gui.showPopup("ErrorPopup", {
                            'title': _t('Unauthorized Access Detected'),
                            'body': _t('Face Recognition Failed..'),
                        });
                        location.reload();
                    }
                });
            }, 300);
        })
    },
});







































































































