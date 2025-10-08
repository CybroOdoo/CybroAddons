/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
const KioskConfirm = require("hr_attendance.kiosk_confirm")
const session = require('web.session');
var rpc = require('web.rpc');
const MODEL_URL = '/face_recognized_attendance_login/static/src/js/weights';
    faceapi.nets.ssdMobilenetv1.loadFromUri(MODEL_URL);
    faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL);
    faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL);
    faceapi.nets.tinyFaceDetector.load(MODEL_URL);
    faceapi.nets.faceLandmark68TinyNet.load(MODEL_URL);
    faceapi.nets.faceExpressionNet.load(MODEL_URL);
    faceapi.nets.ageGenderNet.load(MODEL_URL);

patch(KioskConfirm.prototype,'face_recognized_attendance_login.kiosk',{
    events: {
        "click .o_hr_attendance_back_button": function () { this.do_action(this.next_action, {clear_breadcrumbs: true}); },
        "click .o_hr_attendance_sign_in_out_icon": _.debounce(async function () {
            await this.startWebcam();
        }, 200, true),
    },
//    -------To start the camera-------
    async startWebcam() {
        const video = this.el.querySelector('#video');
        try {
        const video = this.el.querySelector('#video');
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('getUserMedia is not supported in this browser.');
        }
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        video.srcObject = stream;

        video.onloadedmetadata = () => {
            video.play();
        };
        this.faceRecognition(video);
        } catch (error) {
            console.error('An error occurred while accessing the camera:', error);
            this.__parentedParent.notifications.add(
                'Unable to access webcam. Please check your device permissions or use a supported browser.', {
                    title: 'Webcam Error',
                    type: 'danger',
                    sticky: true,
                    className: "p-4"
                }
            );
        }
    },
//    -----To start the face recognition-----------
    async faceRecognition(video) {
        const labeledFaceDescriptors = await this.getLabeledFaceDescriptions(video);
        if (!labeledFaceDescriptors) {
            console.error('No labeled face descriptors available.');
            this.stopWebcamAndDetection();
            return;
        }
        if (!this.faceMatcher) {
            const labeledFaceDescriptors = await this.getLabeledFaceDescriptions();
            this.faceMatcher = new faceapi.FaceMatcher([labeledFaceDescriptors]);
            if (labeledFaceDescriptors && labeledFaceDescriptors.descriptor) {
                this.faceMatcher = new faceapi.FaceMatcher([labeledFaceDescriptors.descriptor]);
            } else {
            console.error("Could not get face descriptor from reference image");
            this.__parentedParent.notification.add("Failed to initialize face recognition, Please upload a new, properly formatted image.", {
                type: "danger",
                title: "Image detection failed!",
            });
            this.stopRecognition(video);
            return;
            }
        }
        let attendanceMarked = false;
        let notificationSent = false;
        this.faceRecognitionInterval = setInterval(async () => {
            try {
                const detections = await faceapi
                    .detectAllFaces(video)
                    .withFaceLandmarks()
                    .withFaceDescriptors();
                if (detections.length === 0) {
                    if (!notificationSent) {
                        this.__parentedParent.notifications.add(
                            'No face detected.', {
                                title: 'Detection Failed!',
                                type: 'danger',
                                sticky: false,
                                className: "p-4"
                            }
                        );
                        notificationSent = true;
                    }
                    this.stopWebcamAndDetection();
                    return;
                }
                detections.forEach((detection) => {
                    const match = this.faceMatcher.findBestMatch(detection.descriptor);
                    if (match._distance < 0.4 && !attendanceMarked) {
                        const modal = this.el.querySelector('#video');
                        if (modal) {
                            modal.style.display = 'none';
                        }
                        attendanceMarked = true;
                        notificationSent = false;
                        this.markAttendance();
                        clearInterval(this.faceRecognitionInterval);
                        this.stopWebcamAndDetection();
                    }
                });
                if (!attendanceMarked && !notificationSent) {
                    this.__parentedParent.notifications.add(
                        'Face is not recognized.', {
                            title: 'No Match!',
                            type: 'danger',
                            sticky: false,
                            className: "p-4"
                        }
                    );
                    notificationSent = true;
                    this.stopWebcamAndDetection();
                }
                } catch (error) {
                    console.error('Error during face recognition:', error);
                    this.stopWebcamAndDetection();
                }
        }, 100);
    },
//    ---------Fetch labeled face descriptions (employee's face data)------
    async getLabeledFaceDescriptions(video) {
        const employee_image_base64 = await rpc.query({
            model: 'hr.employee',
            method: 'get_kiosk_image',
            args: [this.employee_id]
        });
        if (employee_image_base64) {
            const employee_image = new Image();
            employee_image.src = "data:image/jpeg;base64," + employee_image_base64;
            try {
                const detections = await faceapi
                    .detectSingleFace(employee_image)
                    .withFaceLandmarks()
                    .withFaceExpressions()
                    .withFaceDescriptor();
                if (!detections) {
                    console.error('No face detected in the image.');
                    this.__parentedParent.notifications.add(
                            'No face detected in the image.Please upload a new, properly formatted image in the profile.', {
                                title: 'Image detection failed!',
                                type: 'danger',
                                sticky: false,
                                className: "p-4"
                            }
                        );
                    return;
                }
                return detections;
            } catch (error) {
                console.error('Error during face detection:', error);
            }
        } else {
            console.error('No image data found for the employee.');
        }
    },
//    ----------Function to stop webcam and face detection-----
    stopWebcamAndDetection() {
        const video = this.el.querySelector('#video');
        if (video.srcObject) {
            const stream = video.srcObject;
            const tracks = stream.getTracks();
            tracks.forEach(track => track.stop());
            video.srcObject = null; //
        }
        if (this.faceRecognitionInterval) {
            clearInterval(this.faceRecognitionInterval);
            this.faceRecognitionInterval = null;
        }
        this.faceMatcher = null;
    },
//        ------------Redirecting to welcome/checkout page ----------------------------------
    markAttendance() {
        const self = this;
        this._rpc({
            model: 'hr.employee',
            method: 'attendance_manual',
            args: [[this.employee_id], 'hr_attendance.hr_attendance_action_my_attendances']
        }).then((result) => {
            if (result.action) {
                self.do_action(result.action);
            } else if (result.warning) {
                self.do_warn(result.warning);
            }
        }).catch((error) => {
            console.error('Error marking attendance:', error);
        });
    },
})

