/** @odoo-module **/
import { patch } from 'web.utils';
import { ChatterTopbar } from '@mail/components/chatter_topbar/chatter_topbar';
var rpc = require('web.rpc');
patch(ChatterTopbar.prototype, 'mail/static/src/models/chatter/chatter.js', {
    cameraEventListenersSet: false,
    /**
     * Mounts the component and sets up camera event listeners if not already set.
     */
    async mounted() {
        await this._super();
        if (!this.cameraEventListenersSet) {
            this.setupCamera();
            this.cameraEventListenersSet = true;
        }
    },
     /**
     * Sets up event listener for the camera button to open the camera modal and start video streaming.
     */
    setupCamera() {
        const myModal = this.el.querySelector('.modal');
        const cameraButton = this.el.querySelector('#camera_button');

        cameraButton.addEventListener('click', () => {
            myModal.style.display = 'block';

            navigator.mediaDevices.getUserMedia({ audio: false, video: true })
                .then(vidStream => {
                    const video = this.el.querySelector('#videoCam');
                    if ('srcObject' in video) {
                        video.srcObject = vidStream;
                    } else {
                        video.src = window.URL.createObjectURL(vidStream);
                    }
                    video.onloadedmetadata = e => {
                        video.play();
                    };
                    const stopButton = this.el.querySelector('#stop-camera-button');
                    stopButton.addEventListener('click', () => {
                        vidStream.getTracks().forEach(track => {
                            track.stop();
                            myModal.style.display = 'none';
                        });
                    });
                })
        });
    },
     /**
     * Captures an image from the video stream and sends it to the server via RPC.
     * The image is associated with the current chatter thread.
     * @returns {Promise<void>}
     */
    async ImageCapture() {
        const canvas = this.el.querySelector('#canvas');
        const video = this.el.querySelector('#videoCam');
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
        const image_data_url = canvas.toDataURL();
        const regex = /model:([^\s,]+).*id:(\d+)/;
        const children = this.__owl__.children;
        for (const [key, value] of Object.entries(children)) {
            const threadLocalId = value.props.threadLocalId;
            const Match = threadLocalId.match(regex);
            if (Match) {
                const [_, model, id] = Match;
                await rpc.query({
                    model: 'ir.attachment',
                    method: 'chatter_image',
                    args: [model, id, image_data_url],
                });
                location.reload();
            }
            return;
        }
    },
});
