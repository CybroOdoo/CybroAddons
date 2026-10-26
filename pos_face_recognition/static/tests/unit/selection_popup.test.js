import { describe, expect, test } from "@odoo/hoot";
import { setupPosEnv } from "@point_of_sale/../tests/unit/utils";
import { CashierSelectionPopup } from "@pos_hr/app/components/popups/cashier_selection_popup/cashier_selection_popup";
import { mountWithCleanup } from "@web/../tests/web_test_helpers";
import { definePosModels } from "@point_of_sale/../tests/unit/data/generate_model_definitions";

definePosModels();

describe("pos_face_recognition: CashierSelectionPopup extension", () => {
    test("face recognition state initialized in setup", async () => {
        const store = await setupPosEnv();
        const employees = store.models["hr.employee"].getAll();
        const comp = await mountWithCleanup(CashierSelectionPopup, {
            props: {
                close: () => {},
                getPayload: () => {},
                employees,
            },
        });

        expect(typeof comp.webCamModalRef).toBe("function");
        expect(typeof comp.videoRef).toBe("function");
        expect(typeof comp.employeeImageRef).toBe("function");
        expect(comp.faceMatcher).toBe(null);
        expect(comp.intervalId).toBe(null);
        expect(comp.timeoutId).toBe(null);
        expect(comp.stream).toBe(null);
        expect(comp.canvas).toBe(null);
    });

    test("selectEmployee without image raises authentication failed alert", async () => {
        await setupPosEnv();
        let dialogOpened = false;

        const comp = await mountWithCleanup(CashierSelectionPopup, {
            props: {
                close: () => {},
                getPayload: () => {},
                employees: [{ id: 999, name: "Employee No Image" }],
            },
        });

        // Mock dialog service
        comp.dialog = {
            add: (dialogClass, data) => {
                dialogOpened = true;
                expect(data.title).toBe("Authentication failed");
                expect(data.body).toBe("Selected cashier has no image.");
            },
        };

        // Mock loadImage to simulate cashier having no image
        comp.loadImage = async () => {
            comp.have_image = false;
        };

        await comp.selectEmployee({ id: 999, name: "Employee No Image" });
        expect(comp.have_image).toBe(false);
        expect(dialogOpened).toBe(true);
    });

    test("selectEmployee with image opens modal and starts webcam", async () => {
        await setupPosEnv();
        let webcamStarted = false;

        const sampleImage = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7";
        const comp = await mountWithCleanup(CashierSelectionPopup, {
            props: {
                close: () => {},
                getPayload: () => {},
                employees: [{ id: 100, name: "Employee With Image", image: sampleImage }],
            },
        });

        comp.startWebcam = async () => {
            webcamStarted = true;
        };

        await comp.selectEmployee({ id: 100, name: "Employee With Image", image: sampleImage });
        expect(comp.have_image).toBe(true);
        expect(webcamStarted).toBe(true);
    });

    test("cancelFaceRecognition cleans up streams, intervals, and timeouts", async () => {
        const store = await setupPosEnv();
        const employees = store.models["hr.employee"].getAll();
        const comp = await mountWithCleanup(CashierSelectionPopup, {
            props: {
                close: () => {},
                getPayload: () => {},
                employees,
            },
        });

        let trackStopped = false;
        comp.intervalId = setInterval(() => {}, 1000);
        comp.timeoutId = setTimeout(() => {}, 5000);
        comp.stream = {
            getTracks: () => [
                {
                    stop: () => {
                        trackStopped = true;
                    },
                },
            ],
        };

        comp.cancelFaceRecognition();

        expect(comp.intervalId).toBe(null);
        expect(comp.timeoutId).toBe(null);
        expect(comp.stream).toBe(null);
        expect(trackStopped).toBe(true);
    });

    test("handleUnauthorizedLogin cancels face recognition and shows alert", async () => {
        const store = await setupPosEnv();
        const employees = store.models["hr.employee"].getAll();
        let dialogData = null;

        const comp = await mountWithCleanup(CashierSelectionPopup, {
            props: {
                close: () => {},
                getPayload: () => {},
                employees,
            },
        });

        comp.dialog = {
            add: (dialogClass, data) => {
                dialogData = data;
            },
        };

        comp.intervalId = setInterval(() => {}, 1000);
        comp.handleUnauthorizedLogin("Unauthorized login detected!");

        expect(comp.intervalId).toBe(null);
        expect(dialogData).not.toBe(null);
        expect(dialogData.title).toBe("Unauthorized Login");
        expect(dialogData.body).toBe("Unauthorized login detected!");
    });
});
