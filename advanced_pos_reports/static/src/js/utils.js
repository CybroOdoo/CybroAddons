/** @odoo-module **/

export function printReceipt(receiptEl, title, pos) {
    if (!receiptEl) {
        window.print();
        return;
    }
    const iframe = document.createElement("iframe");
    iframe.style.position = "fixed";
    iframe.style.right = "0";
    iframe.style.bottom = "0";
    iframe.style.width = "0";
    iframe.style.height = "0";
    iframe.style.border = "0";
    document.body.appendChild(iframe);
    const doc = iframe.contentWindow.document;
    doc.open();
    doc.write(`
        <!DOCTYPE html>
        <html>
            <head>
                <title>${title || "POS Receipt"}</title>
                <style>
                    @page {
                        margin: 8mm;
                        size: auto;
                    }
                    @media print {
                        html, body {
                            margin: 0 !important;
                            padding: 0 !important;
                            width: 100% !important;
                        }
                        section {
                            overflow: visible !important;
                            max-height: none !important;
                        }
                    }
                    * {
                        box-sizing: border-box;
                    }
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                        margin: 0;
                        padding: 10px;
                        color: #000;
                        background: #fff;
                    }
                    .pos-receipt, .pos-receipt-container {
                        width: 100% !important;
                        max-width: 480px !important;
                        margin: 0 auto !important;
                        padding: 0 !important;
                        font-size: 13px;
                        line-height: 1.4;
                    }
                    section {
                        overflow: visible !important;
                        max-height: none !important;
                    }
                    table {
                        width: 100% !important;
                        border-collapse: collapse !important;
                        table-layout: fixed !important;
                        word-break: break-word !important;
                    }
                    th, td {
                        padding: 4px 6px !important;
                        vertical-align: top;
                    }
                    th {
                        font-weight: bold;
                    }
                    .text-center, .pos-receipt-center-align {
                        text-align: center !important;
                    }
                    .text-end, .text-right {
                        text-align: right !important;
                    }
                    .text-start, .text-left {
                        text-align: left !important;
                    }
                    .w-100 {
                        width: 100% !important;
                    }
                    .pos-receipt-logo {
                        max-width: 150px;
                        height: auto;
                        display: block;
                        margin: 0 auto;
                    }
                    .pos-receipt-contact {
                        text-align: center;
                        font-size: 12px;
                    }
                    .mx-auto {
                        margin-left: auto !important;
                        margin-right: auto !important;
                    }
                    .mt-1 { margin-top: 0.25rem !important; }
                    .mt-2 { margin-top: 0.5rem !important; }
                    .p-4, .p-3 { padding: 0 !important; }
                </style>
            </head>
            <body>${receiptEl.innerHTML}</body>
        </html>
    `);
    doc.close();
    setTimeout(() => {
        if (pos?.ticketPrinter?.printWeb) {
            pos.ticketPrinter.printWeb(iframe);
        } else {
            iframe.contentWindow.focus();
            iframe.contentWindow.print();
        }
        setTimeout(() => {
            iframe.remove();
        }, 2500);
    }, 100);
}
