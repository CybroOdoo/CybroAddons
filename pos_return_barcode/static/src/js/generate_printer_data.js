import { patch } from "@web/core/utils/patch";
import { GeneratePrinterData } from "@point_of_sale/app/utils/printer/generate_printer_data";

const CODE128_PATTERNS = [
    "212222", "222122", "222221", "121223", "121322", "131222",
    "122213", "122312", "132212", "221213", "221312", "231212",
    "112232", "122132", "122231", "113222", "123122", "123221",
    "223211", "221132", "221231", "213212", "223112", "312131",
    "311222", "321122", "321221", "312212", "322112", "322211",
    "212123", "212321", "232121", "111323", "131123", "131321",
    "112313", "132113", "132311", "211313", "231113", "231311",
    "112133", "112331", "132131", "113123", "113321", "133121",
    "313121", "211331", "231131", "213113", "213311", "213131",
    "311123", "311321", "331121", "312113", "312311", "332111",
    "314111", "221411", "431111", "111224", "111422", "121124",
    "121421", "141122", "141221", "112214", "112412", "122114",
    "122411", "142112", "142211", "241211", "221114", "413111",
    "241112", "134111", "111242", "121142", "121241", "114212",
    "124112", "124211", "411212", "421112", "421211", "212141",
    "214121", "412121", "111143", "111341", "131141", "114113",
    "114311", "411113", "411311", "113141", "114131", "311141",
    "411131", "211412", "211214", "211232", "2331112",
];

function encodeCode128(text) {
    const trimmed = String(text || "").trim();
    if (!trimmed) {
        return null;
    }
    const isAllDigits = /^\d+$/.test(trimmed);
    const codes = [];
    if (isAllDigits && trimmed.length % 2 === 0) {
        codes.push(105); // Start C
        for (let i = 0; i < trimmed.length; i += 2) {
            codes.push(parseInt(trimmed.slice(i, i + 2), 10));
        }
    } else {
        codes.push(104); // Start B
        for (let i = 0; i < trimmed.length; i++) {
            const charCode = trimmed.charCodeAt(i);
            codes.push(charCode >= 32 && charCode <= 126 ? charCode - 32 : 0);
        }
    }
    let checksum = codes[0];
    for (let i = 1; i < codes.length; i++) {
        checksum += codes[i] * i;
    }
    codes.push(checksum % 103);
    codes.push(106); // Stop
    return codes;
}

export function generateCode128DataUrl(text, { height = 50 } = {}) {
    const codes = encodeCode128(text);
    if (!codes) {
        return "";
    }
    let totalModules = 0;
    const barSegments = [];
    for (const code of codes) {
        const pattern = CODE128_PATTERNS[code];
        for (let i = 0; i < pattern.length; i++) {
            const width = parseInt(pattern[i], 10);
            if (i % 2 === 0) {
                barSegments.push({ x: totalModules, width });
            }
            totalModules += width;
        }
    }
    const quietZone = 10;
    const svgWidth = totalModules + 2 * quietZone;
    const rects = barSegments
        .map((b) => `<rect x="${b.x + quietZone}" y="0" width="${b.width}" height="${height}" fill="black"/>`)
        .join("");
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${svgWidth} ${height}" width="${svgWidth}" height="${height}">${rects}</svg>`;
    try {
        return "data:image/svg+xml;base64," + window.btoa(svg);
    } catch {
        return "";
    }
}

patch(GeneratePrinterData.prototype, {
    generateReceiptData() {
        const data = super.generateReceiptData(...arguments);
        const rawBarcode = this.order.barcode;
        const barcode =
            rawBarcode && rawBarcode !== "undefined"
                ? rawBarcode
                : this.order.pos_reference
                ? this.order.pos_reference.replace(/Order/g, "").replace(/[- ]/g, "").trim()
                : "";
        if (barcode) {
            data.image.pos_barcode = barcode;
            data.image.pos_barcode_src =
                generateCode128DataUrl(barcode) ||
                "/report/barcode/Code128/" + encodeURIComponent(barcode);
        }
        if (!data.image.get) {
            data.image.get = function (key) {
                return this[key];
            };
        }
        return data;
    },
});
