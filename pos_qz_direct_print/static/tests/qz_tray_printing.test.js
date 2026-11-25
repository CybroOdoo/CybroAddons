import { expect, test } from "@odoo/hoot";
import { PosTicketPrinterPlugin } from "@point_of_sale/app/plugins/pos_ticket_printer_plugin";
import { patchWithCleanup } from "@web/../tests/web_test_helpers";
import "@pos_qz_direct_print/app/services/pos_ticket_printer_patch";

function setupPrinting({ printerName = "Receipt Printer", hardwarePrinter, fail = false } = {}) {
    let connected = false;
    patchWithCleanup(globalThis, {
        qz: {
            websocket: {
                isActive: () => connected,
                async connect() {
                    expect.step("connect");
                    connected = true;
                },
            },
            configs: {
                create(name) {
                    expect(name).toBe(printerName);
                    return { name };
                },
            },
            async print(config, data) {
                expect.step("QZ print");
                expect(config).toEqual({ name: printerName });
                expect(data).toEqual([
                    { type: "pixel", format: "image", flavor: "base64", data: "dGVzdA==" },
                ]);
                if (fail) {
                    throw new Error("Printer unavailable");
                }
            },
        },
    });
    const plugin = Object.create(PosTicketPrinterPlugin.prototype, {
        config: { value: { system_printer_name: printerName, receipt_printer_ids: [] } },
        defaultPrinter: { value: hardwarePrinter },
        notification: { value: { add: () => expect.step("warning") } },
    });
    plugin.generateImage = async () => ({ toDataURL: () => "data:image/png;base64,dGVzdA==" });
    plugin.printWeb = () => expect.step("browser print");
    plugin.print = async ({ printer }) => {
        expect(printer).toBe(hardwarePrinter);
        expect.step("hardware print");
        return { successful: true };
    };
    return plugin;
}

test("Sends the rendered receipt to the configured QZ Tray printer", async () => {
    const plugin = setupPrinting();
    expect(await plugin.printWithFallback({ iframe: {} })).toEqual({ successful: true });
    expect.verifySteps(["connect", "QZ print"]);
});

test("Shares the QZ Tray connection across overlapping receipts", async () => {
    const plugin = setupPrinting();
    await Promise.all([
        plugin.printWithFallback({ iframe: {} }),
        plugin.printWithFallback({ iframe: {} }),
    ]);
    expect.verifySteps(["connect", "QZ print", "QZ print"]);
});

test("Falls back to the browser after QZ Tray rejects the print job", async () => {
    const plugin = setupPrinting({ fail: true });
    await plugin.printWithFallback({ iframe: {} });
    expect.verifySteps(["connect", "QZ print", "warning", "browser print"]);
});

test("Respects disabled browser fallback after a QZ Tray failure", async () => {
    const plugin = setupPrinting({ fail: true });
    await plugin.printWithFallback({ iframe: {}, webFallback: false });
    expect.verifySteps(["connect", "QZ print", "warning"]);
});

test("Uses the standard browser path when the QZ Tray printer is blank", async () => {
    const plugin = setupPrinting({ printerName: "" });
    await plugin.printWithFallback({ iframe: {} });
    expect.verifySteps(["browser print"]);
});

test("Gives the configured hardware printer priority over QZ Tray", async () => {
    const plugin = setupPrinting({ hardwarePrinter: { id: 1 } });
    expect(await plugin.printWithFallback({ iframe: {} })).toEqual({ successful: true });
    expect.verifySteps(["hardware print"]);
});
