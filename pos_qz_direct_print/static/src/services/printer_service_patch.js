/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosPrinterService } from "@point_of_sale/app/printer/pos_printer_service";
import { jsonrpc } from "@web/core/network/rpc_service";

/**
 * Temporarily intercepts window.fetch to stub out Odoo CDN font requests
 * that return 404. The html-to-image canvas renderer fetches all CSS
 * resources (including @font-face fonts). Missing fonts cause net errors
 * that can delay or corrupt canvas capture. This wrapper silently returns
 * an empty CSS response for any font.odoocdn.com request.
 *
 * Returns the original fetch so the caller can restore it in a finally block.
 */
function installFontFetchGuard() {
    const originalFetch = window.fetch;
    window.fetch = async (url, ...args) => {
        if (
            typeof url === 'string' &&
            (url.includes('fonts.odoocdn.com') || url.includes('fonts.gstatic.com'))
        ) {
            // Return an empty font/CSS response to prevent 404 noise
            return new Response(new Blob([''], { type: 'text/css' }), {
                status: 200,
                headers: { 'Content-Type': 'text/css' },
            });
        }
        return originalFetch(url, ...args);
    };
    return originalFetch;
}

patch(PosPrinterService.prototype, {
    /**
     * Override print to intercept the POS print flow.
     * If a system_printer_name is configured, convert the component to a JPEG
     * and print silently via QZ Tray or the server-side CUPS printer.
     */
    async print(component, props, options = {}) {
        const printerName = this.pos?.config?.system_printer_name || '';

        // If no system printer is configured, use standard Odoo print flow
        if (!printerName) {
            return super.print(...arguments);
        }

        // Try printing via QZ Tray if the library is available
        if (typeof qz !== 'undefined') {
            try {
                // Configure QZ Tray to run without a signing certificate
                qz.security.setCertificatePromise((resolve) => {
                    resolve();
                });
                qz.security.setSignatureAlgorithm("SHA512");
                qz.security.setSignaturePromise(() => {
                    return (resolve) => resolve();
                });

                // Suppress CDN font 404s during canvas capture
                const originalFetch = installFontFetchGuard();
                let base64Image;
                try {
                    // Render component to JPEG base64 using Odoo's native renderer.
                    // Note: addClass only supports a single CSS class token (no spaces).
                    base64Image = await this.renderer.toJpeg(
                        component,
                        props,
                        { addClass: "pos-receipt-print" }
                    );
                } finally {
                    // Always restore fetch after rendering
                    window.fetch = originalFetch;
                }

                const cleanBase64 = base64Image.includes(',')
                    ? base64Image.split(',')[1]
                    : base64Image;

                // Connect to QZ Tray if not already connected
                if (!qz.websocket.isActive()) {
                    await qz.websocket.connect();
                }

                // Configure the printer and send print data as a pixel image
                const config = qz.configs.create(printerName);
                const data = [{
                    type: 'pixel',
                    format: 'image',
                    flavor: 'base64',
                    data: cleanBase64,
                }];

                console.log(
                    `🚀 Sending print job to QZ Tray for printer: ${printerName}`
                );
                await qz.print(config, data);

                return true;

            } catch (e) {
                console.error("❌ QZ Tray Print Error:", e);
                console.warn("⚠️ Falling back to server-side CUPS print...");
            } finally {
                // Disconnect QZ Tray
                try {
                    if (typeof qz !== 'undefined' && qz.websocket.isActive()) {
                        await qz.websocket.disconnect();
                    }
                } catch (err) {
                    console.warn("QZ Tray disconnect error:", err);
                }
            }
        } else {
            console.warn("QZ Tray library not loaded. Trying server-side CUPS print...");
        }

        // Fallback: print via server-side CUPS (lp)
        return await this._printViaServer(component, props, printerName);
    },

    /**
     * Server-side fallback: render receipt to JPEG and call the Odoo backend
     * which prints via the CUPS `lp` command.
     */
    async _printViaServer(component, props, printerName) {
        const originalFetch = installFontFetchGuard();
        let base64Image;
        try {
            base64Image = await this.renderer.toJpeg(
                component,
                props,
                { addClass: "pos-receipt-print" }
            );
        } catch (e) {
            console.error("Receipt render error in server fallback:", e);
            window.fetch = originalFetch;
            return super.print(component, props);
        } finally {
            window.fetch = originalFetch;
        }

        const cleanBase64 = base64Image.includes(',')
            ? base64Image.split(',')[1]
            : base64Image;

        const configId = this.pos?.config?.id;
        if (!configId) {
            console.warn("No POS config ID found, falling back to browser print.");
            return super.print(component, props);
        }

        try {
            const result = await jsonrpc("/web/dataset/call_kw", {
                model: "pos.config",
                method: "action_print_to_system",
                args: [configId, cleanBase64],
                kwargs: {},
            });

            if (result) {
                return true;
            } else {
                console.warn("Server print returned false, falling back to browser print.");
                return super.print(component, props);
            }
        } catch (e) {
            console.error("Server-side CUPS print error:", e);
            return super.print(component, props);
        }
    },
});