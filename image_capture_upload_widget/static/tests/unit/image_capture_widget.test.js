import { describe, expect, test } from "@odoo/hoot";
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import {
    ImageCaptureComponent,
    imageCapture,
    imageCaptureProps,
    fileTypeMagicWordMap,
} from "@image_capture_upload_widget/js/image_capture";

describe("Image Capture Widget - JS Unit Tests", () => {
    describe.current.tags("desktop");

    test("imageCapture widget definition is registered in fields registry", () => {
        const registered = registry.category("fields").get("capture_image");
        expect(registered).toBe(imageCapture, {
            message: "'capture_image' widget must be registered in the 'fields' category",
        });
        expect(imageCapture.supportedTypes).toEqual(["binary"]);
        expect(imageCapture.component).toBe(ImageCaptureComponent);
        expect(imageCapture.fieldDependencies).toEqual([{ name: "write_date", type: "datetime" }]);
    });

    test("extractProps handles field attributes and options correctly", () => {
        const extracted = imageCapture.extractProps({
            attrs: { width: 120, height: 100 },
            options: {
                preview_image: "image_128",
                accepted_file_extensions: "image/png,image/jpeg",
                size: [80, 80],
                reload: false,
            },
        });

        expect(extracted.previewImage).toBe("image_128");
        expect(extracted.acceptedFileExtensions).toBe("image/png,image/jpeg");
        expect(extracted.width).toBe(80);
        expect(extracted.height).toBe(80);
        expect(extracted.reload).toBe(false);
    });

    test("ImageCaptureComponent is a valid OWL Component with namespaced template", () => {
        expect(Object.getPrototypeOf(ImageCaptureComponent)).toBe(Component);
        expect(ImageCaptureComponent.template).toBe("image_capture_upload_widget.CaptureImage");
    });

    test("stopCamera properly stops tracks and resets camera state", () => {
        let trackStopped = false;
        const mockTrack = {
            stop() {
                trackStopped = true;
            },
        };
        const mockStream = {
            getTracks() {
                return [mockTrack];
            },
        };

        const mockComponent = {
            state: {
                stream: mockStream,
                isCameraOpen: true,
                hasSnapshot: true,
            },
            playerEl: { srcObject: mockStream },
            stopTracksOnMediaStream: ImageCaptureComponent.prototype.stopTracksOnMediaStream,
        };

        ImageCaptureComponent.prototype.stopCamera.call(mockComponent);

        expect(trackStopped).toBe(true, { message: "MediaStream track must be stopped" });
        expect(mockComponent.state.stream).toBe(null);
        expect(mockComponent.state.isCameraOpen).toBe(false);
        expect(mockComponent.state.hasSnapshot).toBe(false);
        expect(mockComponent.playerEl.srcObject).toBe(null);
    });

    test("onFileRemove clears value and updates record", () => {
        let updatedRecord = null;
        const mockComponent = {
            state: { isValid: false },
            lastURL: "https://example.com/image.png",
            rawCacheKey: "2026-10-22",
            props: {
                name: "image_1920",
                record: {
                    update(val) {
                        updatedRecord = val;
                    },
                },
            },
        };

        ImageCaptureComponent.prototype.onFileRemove.call(mockComponent);

        expect(mockComponent.state.isValid).toBe(true);
        expect(mockComponent.lastURL).toBe(null);
        expect(mockComponent.rawCacheKey).toBe(null);
        expect(updatedRecord).toEqual({ image_1920: false });
    });

    test("onFileUploaded updates record with base64 data", async () => {
        let updatedRecord = null;
        const mockComponent = {
            state: { isValid: false },
            lastURL: "https://example.com/cached.png",
            rawCacheKey: "old_key",
            props: {
                name: "image_1920",
                record: {
                    update(val) {
                        updatedRecord = val;
                    },
                },
            },
        };

        await ImageCaptureComponent.prototype.onFileUploaded.call(mockComponent, "my_base64_string");

        expect(mockComponent.state.isValid).toBe(true);
        expect(mockComponent.lastURL).toBe(null);
        expect(mockComponent.rawCacheKey).toBe(null);
        expect(updatedRecord).toEqual({ image_1920: "my_base64_string" });
    });

    test("onClickCaptureImage draws video frame to canvas and sets hasSnapshot", () => {
        let drawImageArgs = null;
        const mockCanvas = {
            width: 0,
            height: 0,
            getContext() {
                return {
                    drawImage(...args) {
                        drawImageArgs = args;
                    },
                };
            },
            toDataURL(mime) {
                return `data:${mime};base64,captured_pixel`;
            },
        };
        const mockVideo = {
            videoWidth: 640,
            videoHeight: 480,
        };

        const mockComponent = {
            playerEl: mockVideo,
            snapshotEl: mockCanvas,
            state: { hasSnapshot: false },
            capturedUrl: null,
        };

        ImageCaptureComponent.prototype.onClickCaptureImage.call(mockComponent);

        expect(mockCanvas.width).toBe(640);
        expect(mockCanvas.height).toBe(480);
        expect(drawImageArgs).not.toBe(null);
        expect(mockComponent.capturedUrl).toBe("data:image/png;base64,captured_pixel");
        expect(mockComponent.state.hasSnapshot).toBe(true);
    });

    test("onClickSaveImage strips data URI prefix and triggers upload", async () => {
        let uploadedData = null;
        let cameraStopped = false;

        const mockComponent = {
            capturedUrl: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAE=",
            async onFileUploaded(payload) {
                uploadedData = payload;
            },
            stopCamera() {
                cameraStopped = true;
            },
            notification: { add() {} },
        };

        await ImageCaptureComponent.prototype.onClickSaveImage.call(mockComponent);

        expect(uploadedData).toBe("iVBORw0KGgoAAAANSUhEUgAAAAE=", {
            message: "Should strip data URI scheme and send only base64 data to onFileUploaded",
        });
        expect(cameraStopped).toBe(true);
    });

    test("getUrl returns placeholder when record has no image data", () => {
        const mockComponent = {
            props: {
                name: "image_1920",
                reload: true,
                record: { data: { image_1920: false } },
            },
            state: { isValid: true },
        };

        const url = ImageCaptureComponent.prototype.getUrl.call(mockComponent);
        expect(url).toBe("/web/static/img/placeholder.png");
    });

    test("getUrl returns data URL unchanged when content starts with data:", () => {
        const dataUrl = "data:image/png;base64,test_content";
        const mockComponent = {
            props: {
                name: "image_1920",
                reload: true,
                record: { data: { image_1920: dataUrl } },
            },
            state: { isValid: true },
        };

        const url = ImageCaptureComponent.prototype.getUrl.call(mockComponent);
        expect(url).toBe(dataUrl);
    });
});
