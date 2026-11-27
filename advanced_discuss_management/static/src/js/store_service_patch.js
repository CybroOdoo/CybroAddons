import { Store } from "@mail/core/common/store_service";

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

patch(Store.prototype, {
    /**
     * Ask for camera/microphone access before starting a meeting so that the user
     * gets a clear message when the browser blocks the devices.
     *
     * @override
     */
    async requestStartMeeting() {
        // The camera check can take a while (permission prompt) and the meeting creation
        // too: ignore the clicks made meanwhile instead of creating one meeting per click.
        if (this._admStartingMeeting) {
            return;
        }
        this._admStartingMeeting = true;
        try {
            if (!(await this._admCheckCameraAccess())) {
                return;
            }
            return await super.requestStartMeeting(...arguments);
        } finally {
            this._admStartingMeeting = false;
        }
    },

    /**
     * @returns {Promise<boolean>} false when the meeting must not be started
     */
    async _admCheckCameraAccess() {
        const notification = this.env.services.notification;
        if (!navigator.mediaDevices?.getUserMedia) {
            notification.add(
                _t(
                    "Camera access is only available on secure connections (HTTPS) or localhost. Please check your URL."
                ),
                { type: "warning" }
            );
            return false;
        }
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            // Only needed to verify the permission: release the devices immediately.
            stream.getTracks().forEach((track) => track.stop());
        } catch (err) {
            if (["NotAllowedError", "PermissionDeniedError"].includes(err.name)) {
                notification.add(
                    _t(
                        "Camera access was denied. Please enable it in your browser settings to start a meeting."
                    ),
                    { type: "danger" }
                );
                return false;
            }
            // Other errors (no device, device busy...): Odoo's call logic reports them.
        }
        return true;
    },
});
