odoo.define('pos_face_recognition.FaceLoginScreen', function (require) {
    "use strict";
    const LoginScreen = require('pos_hr.LoginScreen');
    const {patch} = require('web.utils');
    const {_t} = require('web.core');
    const {useService} = require("@web/core/utils/hooks");
    const {useState} = owl.hooks;
    const {useRef} = owl.hooks;
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
            // super.setup(...arguments);
            this.state = useState({
                imageUrl: false
            })
            this.rpc = useService("rpc");
            this.root = useRef("LoginRoot");
            this.faceMatcher = null;
        },

        // overriding back function
        async back() {
            await this.loadImage()
        },
         // overriding selectCashier function
        async selectCashier() {
            const list = this.env.pos.employees.map((employee) => {
                return {
                    id: employee.id,
                    item: employee,
                    label: employee.name,
                    isSelected: false,
                };
            });

            const employee = await this.selectEmployee(list);
            if (employee) {
                this.env.pos.set_cashier(employee);
                this.back();
            }
            this.root.el.querySelector('#login-screen').style.zIndex = -1
        },

        // Function to loadimage
        async loadImage() {
            var cashier_id = this.env.pos.changed.cashier.id
            await ajax.jsonRpc('/cashier/image/', 'call', {
                cashier_id: cashier_id,
            }).then(async data => {
                if (data) {
                    this.have_image = data
                    const employee_image = this.root.el.querySelector('#employee_image')
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
            const employee_image = this.root.el.querySelector('#employee_image');
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
                            const modal = document.getElementById('WebCamModal');
                            if (modal) {
                                modal.style.display = 'none';
                                this.props.resolve({
                                    confirmed: false,
                                    payload: false
                                });
                                this.trigger('close-temp-screen');
                                this.env.pos.hasLoggedIn = true;
                                posbus.trigger('start-cash-control');
                                video.srcObject.getTracks().forEach(track => track.stop());
                                canvas.remove();
                            }
                        } else {
                        }
                    });
                }, 100);
            })
        },
    });
});