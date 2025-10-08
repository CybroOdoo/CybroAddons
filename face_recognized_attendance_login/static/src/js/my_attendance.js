odoo.define('face_recognized_attendance_login.my_attendance', function(require) {
    "use strict";
    // Required Odoo dependencies
    var core = require('web.core');
    var Widget = require('web.Widget');
    var rpc = require('web.rpc');
    var MyAttendances = require('hr_attendance.my_attendances');
    var _t = core._t;
    var login = 0;
    const MODEL_URL = '/face_recognized_attendance_login/static/src/js/weights';
    // Load face-api.js models
    faceapi.nets.ssdMobilenetv1.loadFromUri(MODEL_URL);
    faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL);
    faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL);
    faceapi.nets.tinyFaceDetector.load(MODEL_URL);
    faceapi.nets.faceLandmark68TinyNet.load(MODEL_URL);
    faceapi.nets.faceExpressionNet.load(MODEL_URL);
    faceapi.nets.ageGenderNet.load(MODEL_URL);
    // Extend MyAttendances widget
    MyAttendances.include({
         events: _.extend({}, MyAttendances.prototype.events, {
            'click #close_qr_scanner': 'stopWebcamAndDetection',
         }),
        update_attendance: async function() {
            this.faceMatcher = null;
            this.el.querySelector('.close_button').classList.remove('d-none'); // Show the close button
            await this.startWebcam();
        },
//--------------------------------------------------------------------
        async startWebcam() {
            const video = this.el.querySelector('#video');
            console.log("navigator",navigator)
            try {
                if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                    throw new Error('Webcam access is not supported or allowed in this browser.');
                }
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
                video.srcObject = stream;
                video.onloadedmetadata = () => {
                    video.play();
                };
                this.faceRecognition(video);
            } catch (error) {
                this.el.querySelector('.close_button').classList.add('d-none');
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
// --------------------Function to stop webcam and face detection------------
        stopWebcamAndDetection() {
            const video = this.el.querySelector('#video');
            this.el.querySelector('.close_button').classList.add('d-none');
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
            console.log('Camera and detection stopped.');
        },

//------------------ Fetch labeled face descriptions (employee's face data)------
        async getLabeledFaceDescriptions(video) {
            const employee_image_base64 = await rpc.query({
                model: 'hr.employee',
                method: 'get_login_screen',
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
                        console.log(detections)
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
//----------------------------- Face recognition logic---------------
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
                            notificationSent = true; // Prevent duplicate notifications
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
                            attendanceMarked = true; // Set flag to prevent re-matching
                            notificationSent = false; // Reset notification flag
                            this.markAttendance();
                            clearInterval(this.faceRecognitionInterval);
                            this.stopWebcamAndDetection(); // Stop webcam and detection
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
//        ------------Redirecting to welcome/checkout page ----------------------------------
        markAttendance() {
            const self = this;
            this._rpc({
                model: 'hr.employee',
                method: 'attendance_manual',
                args: [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances']
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
    });
});
