/** @odoo-module **/

let pendingConnection;

async function connect(qz) {
    if (pendingConnection) {
        await pendingConnection;
    } else if (!qz.websocket.isActive()) {
        // Share the connection attempt across simultaneous receipt jobs.
        pendingConnection = qz.websocket.connect();
        try {
            await pendingConnection;
        } finally {
            pendingConnection = undefined;
        }
    }
}

export class QzTrayPrinter {
    constructor(printerName) {
        this.printerName = printerName;
    }

    async print(image) {
        const qz = globalThis.qz;
        const data = image.toDataURL("image/png").split(",")[1];
        await connect(qz);
        await qz.print(qz.configs.create(this.printerName), [
            { type: "pixel", format: "image", flavor: "base64", data },
        ]);
    }
}
