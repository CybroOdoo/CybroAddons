import { CameraDialog } from "@chatter_camera/js/chatter_camera";
import { describe, expect, test } from "@odoo/hoot";
import { animationFrame } from "@odoo/hoot-mock";
import { click, contains, mountWithCleanup } from "@web/../tests/web_test_helpers";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import { Chatter } from "@mail/chatter/web_portal_project/chatter";

describe.current.tags("desktop");
defineMailModels();

test("CameraDialog renders video feed, capture button, and cancel button", async () => {
    let closed = false;
    const originalMediaDevices = navigator.mediaDevices;
    const mockStream = {
        getTracks: () => [{ stop: () => {} }],
    };
    navigator.mediaDevices = {
        getUserMedia: async () => mockStream,
    };

    try {
        await mountWithCleanup(CameraDialog, {
            props: {
                onCapture: () => {},
                close: () => {
                    closed = true;
                },
            },
        });
        await animationFrame();

        await contains(".o_chatter_camera_container");
        await contains("video.o_chatter_camera_video");
        await contains("button#click_photo");
        await contains("button:contains('Cancel')");
        expect(closed).toBe(false);
    } finally {
        navigator.mediaDevices = originalMediaDevices;
    }
});

test("CameraDialog capturePhoto flow generates JPEG File and triggers onCapture and close", async () => {
    let capturedFile = null;
    let isClosed = false;

    const originalMediaDevices = navigator.mediaDevices;
    const mockStream = {
        getTracks: () => [{ stop: () => {} }],
    };
    navigator.mediaDevices = {
        getUserMedia: async () => mockStream,
    };

    try {
        const dialog = await mountWithCleanup(CameraDialog, {
            props: {
                onCapture: (file) => {
                    capturedFile = file;
                    expect.step("onCapture");
                },
                close: () => {
                    isClosed = true;
                    expect.step("close");
                },
            },
        });
        await animationFrame();

        // Mock canvas toBlob to return a valid dummy Blob
        const canvas = dialog.canvasRef();
        if (canvas) {
            canvas.toBlob = (callback) => {
                callback(new Blob(["test_jpeg_data"], { type: "image/jpeg" }));
            };
        }

        await click("button#click_photo");
        await animationFrame();

        expect.verifySteps(["onCapture", "close"]);
        expect(capturedFile).toBeInstanceOf(File);
        expect(capturedFile.type).toBe("image/jpeg");
        expect(capturedFile.name.startsWith("capture_")).toBe(true);
        expect(capturedFile.name.endsWith(".jpeg")).toBe(true);
        expect(isClosed).toBe(true);
    } finally {
        navigator.mediaDevices = originalMediaDevices;
    }
});

test("Chatter onClickCamera patch opens CameraDialog and uploads captured file", async () => {
    let dialogComponent = null;
    let dialogProps = null;
    let uploadedFile = null;

    const mockDialogService = {
        add: (ComponentClass, props) => {
            dialogComponent = ComponentClass;
            dialogProps = props;
            expect.step("dialog.add");
        },
    };

    const mockAttachmentUploader = {
        uploadFile: async (file) => {
            uploadedFile = file;
            expect.step("uploadFile");
        },
    };

    const mockChatter = Object.create(Chatter.prototype);
    mockChatter.dialog = mockDialogService;
    mockChatter.state = {
        thread: { id: 1, model: "res.partner" },
        activePanel: null,
    };
    mockChatter.attachmentUploader = mockAttachmentUploader;
    mockChatter.CHATTER_PANEL = { ATTACHMENT: "attachments" };
    mockChatter.hasParentReloadOnAttachmentsChanged = true;
    mockChatter.reloadParentView = () => {
        expect.step("reloadParentView");
    };

    // Trigger chatter camera button action
    mockChatter.onClickCamera();
    expect.verifySteps(["dialog.add"]);
    expect(dialogComponent).toBe(CameraDialog);

    // Simulate onCapture callback triggered by the camera dialog
    const dummyFile = new File(["photo_bytes"], "capture_test.jpeg", { type: "image/jpeg" });
    await dialogProps.onCapture(dummyFile);

    expect.verifySteps(["uploadFile", "reloadParentView"]);
    expect(uploadedFile).toBe(dummyFile);
    expect(mockChatter.state.activePanel).toBe("attachments");
});

test("CameraDialog stopCamera cleanly terminates active MediaStream tracks", async () => {
    let trackStopped = false;
    const mockStream = {
        getTracks: () => [
            {
                stop: () => {
                    trackStopped = true;
                    expect.step("track_stopped");
                },
            },
        ],
    };
    const originalMediaDevices = navigator.mediaDevices;
    navigator.mediaDevices = {
        getUserMedia: async () => mockStream,
    };

    try {
        const dialog = await mountWithCleanup(CameraDialog, {
            props: {
                onCapture: () => {},
                close: () => {},
            },
        });
        await animationFrame();

        dialog.stopCamera();
        expect.verifySteps(["track_stopped"]);
        expect(trackStopped).toBe(true);
    } finally {
        navigator.mediaDevices = originalMediaDevices;
    }
});
