import { registry } from "@web/core/registry";

/**
 * Tour test for image_capture_upload_widget:
 * 1. Opens the partner form view.
 * 2. Verifies that the custom image capture widget is rendered.
 * 3. Checks that the camera capture floating button exists.
 * 4. Clicks the camera capture button to trigger the camera modal dialog.
 * 5. Verifies that the capture modal dialog, video container and action buttons are displayed.
 * 6. Closes the modal via the close/cancel button.
 * 7. Confirms that the modal is closed and returns to the form view.
 */
registry.category("web_tour.tours").add("image_capture_tour", {
    steps: () => [
        {
            content: "Verify capture image widget container is displayed on the form",
            trigger: ".capture-container",
        },
        {
            content: "Verify camera capture button is rendered in widget",
            trigger: ".camera-floating-buttons .o_upload_image_button",
        },
        {
            content: "Click camera button to open capture modal dialog",
            trigger: ".camera-floating-buttons .o_upload_image_button",
            run: "click",
        },
        {
            content: "Verify camera capture modal dialog is displayed",
            trigger: ".capture-modal-dialog",
        },
        {
            content: "Verify video feed container exists inside camera modal",
            trigger: ".capture-modal-dialog .capture-video-container",
        },
        {
            content: "Click close button to close camera modal",
            trigger: ".capture-modal-dialog .btn-close",
            run: "click",
        },
        {
            content: "Verify modal is dismissed and camera button remains visible",
            trigger: ".camera-floating-buttons .o_upload_image_button",
        },
    ],
});
