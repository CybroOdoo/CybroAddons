import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("chatter_camera_tour", {
    steps: () => [
        {
            content: "Check that the camera button is present in the chatter topbar and click it",
            trigger: "button#camera_button",
            run: "click",
        },
        {
            content: "Verify that CameraDialog is opened with video container",
            trigger: ".o_chatter_camera_container video.o_chatter_camera_video, .modal-title:contains('Camera')",
        },
        {
            content: "Verify capture and cancel buttons exist, then cancel and close dialog",
            trigger: ".modal-footer button:contains('Cancel')",
            run: "click",
        },
    ],
});
