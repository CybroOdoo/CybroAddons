/** @odoo-module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { loadJS } from "@web/core/assets";
import { rpc } from "@web/core/network/rpc";

let isScanning = false;
let isProcessing = false;

async function startBarcodeScanner() {
    const container = document.querySelector("#barcode_id");
    if (!container) return;

    if (!navigator.mediaDevices || typeof navigator.mediaDevices.getUserMedia !== "function") {
        container.innerHTML = `
            <div class="alert alert-warning mb-0 text-start">
                <strong><i class="oi oi-fw me-1" data-icon="warning"></i>Camera unavailable:</strong>
                Camera access requires a secure connection (HTTPS or localhost). Please ensure you are browsing via HTTPS or on localhost.
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="d-flex flex-column align-items-center justify-content-center py-4">
            <div class="spinner-border text-primary mb-2" role="status"></div>
            <p class="text-muted mb-0">Starting camera...</p>
        </div>
    `;

    try {
        if (!window.Quagga) {
            await loadJS("https://cdn.jsdelivr.net/npm/@ericblade/quagga2@1.8.4/dist/quagga.min.js");
        }
    } catch (e) {
        container.innerHTML = `<div class="alert alert-danger mb-0">Failed to load barcode scanner library. Please check your internet connection.</div>`;
        return;
    }

    const Quagga = window.Quagga;
    if (!Quagga) {
        container.innerHTML = `<div class="alert alert-danger mb-0">Barcode scanner library is unavailable.</div>`;
        return;
    }

    // Stop any previous running scanner
    try {
        Quagga.stop();
    } catch (e) {
        console.debug("Error stopping previous scanner instance:", e);
    }
    isScanning = false;
    isProcessing = false;

    const initQuagga = (videoConstraints) => {
        Quagga.init(
            {
                inputStream: {
                    name: "Live",
                    type: "LiveStream",
                    constraints: {
                        video: videoConstraints,
                    },
                    numOfWorkers: navigator.hardwareConcurrency ? Math.min(navigator.hardwareConcurrency, 4) : 2,
                    target: container,
                },
                decoder: {
                    readers: [
                        "ean_reader",
                        "ean_8_reader",
                        "code_128_reader",
                        "upc_reader",
                        "upc_e_reader",
                    ],
                },
                locate: true,
            },
            function (err) {
                if (err) {
                    console.warn("Quagga init failed with:", videoConstraints, err);
                    // If environment camera fails (e.g. laptop/desktop with only front webcam), retry with any camera
                    if (typeof videoConstraints === "object" && videoConstraints.facingMode) {
                        initQuagga(true);
                        return;
                    }
                    let msg = "Unable to access camera. Please allow camera permissions in your browser.";
                    if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
                        msg = "Camera permission was denied. Please allow camera access in your browser settings (look for the camera icon in your address bar).";
                    } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
                        msg = "No camera was detected on this device.";
                    }
                    container.innerHTML = `<div class="alert alert-danger mb-0 text-start">${msg}</div>`;
                    return;
                }
                container.querySelectorAll(".spinner-border, p, .alert").forEach(el => el.remove());
                Quagga.start();
                isScanning = true;
            }
        );
    };

    // Try environment camera first, then fall back to any available camera
    initQuagga({ facingMode: "environment" });

    Quagga.offDetected();
    Quagga.onDetected(function (result) {
        if (isProcessing) return;
        const last_code = result && result.codeResult && result.codeResult.code;
        if (!last_code) return;

        isProcessing = true;
        try {
            Quagga.stop();
        } catch (e) {
            console.debug("Error stopping scanner on barcode detect:", e);
        }
        isScanning = false;

        hideModal(document.getElementById("barcodeModal"));

        rpc("/shop/barcode/product", { last_code: last_code }).then(function (result) {
            if (!result || !result.url) {
                showModal(document.getElementById("noProductModal"));
            } else {
                window.location.href = result.url;
            }
        }).catch(function (err) {
            console.error("Error fetching product by barcode:", err);
            isProcessing = false;
        });
    });
}

function stopBarcodeScanner() {
    if (window.Quagga && isScanning) {
        try {
            window.Quagga.stop();
        } catch (e) {
            console.debug("Error stopping barcode scanner:", e);
        }
        isScanning = false;
    }
    const container = document.querySelector("#barcode_id");
    if (container) {
        container.innerHTML = `
            <p class="text-muted mb-0">Point your scanner or camera at a barcode to search for a product.</p>
        `;
    }
}

function hideModal(modalEl) {
    if (!modalEl) return;
    const ModalClass = window.Modal || (typeof bootstrap !== "undefined" ? bootstrap.Modal : null);
    if (ModalClass && typeof ModalClass.getInstance === "function") {
        const instance = ModalClass.getInstance(modalEl);
        if (instance) {
            instance.hide();
            return;
        }
    }
    const closeBtn = modalEl.querySelector('[data-bs-dismiss="modal"]');
    if (closeBtn) {
        closeBtn.click();
        return;
    }
    modalEl.classList.remove("show");
    modalEl.style.display = "none";
    document.querySelectorAll(".modal-backdrop").forEach(b => b.remove());
    document.body.classList.remove("modal-open");
    document.body.style.removeProperty("overflow");
    document.body.style.removeProperty("padding-right");
}

function showModal(modalEl) {
    if (!modalEl) return;
    const ModalClass = window.Modal || (typeof bootstrap !== "undefined" ? bootstrap.Modal : null);
    if (ModalClass) {
        const instance = ModalClass.getInstance(modalEl) || (typeof ModalClass.getOrCreateInstance === "function" ? ModalClass.getOrCreateInstance(modalEl) : new ModalClass(modalEl));
        if (instance) {
            instance.show();
            return;
        }
    }
    modalEl.classList.add("show");
    modalEl.style.display = "block";
    document.body.classList.add("modal-open");
}

// Attach event listener to handle modal hide
if (typeof document !== "undefined") {
    document.addEventListener("hidden.bs.modal", (ev) => {
        if (ev.target && ev.target.id === "barcodeModal") {
            stopBarcodeScanner();
        }
    });
}

export class WebsiteSaleBarcode extends Interaction {
    static selector = ".o_wsale_apply_barcode";
    dynamicContent = {
        _root: {
            "t-on-click": () => {
                const modal = document.getElementById("barcodeModal");
                if (modal) {
                    const onShown = () => {
                        modal.removeEventListener("shown.bs.modal", onShown);
                        startBarcodeScanner();
                    };
                    modal.addEventListener("shown.bs.modal", onShown, { once: true });
                } else {
                    startBarcodeScanner();
                }
            },
        },
    };
}

registry.category("public.interactions").add("ecommerce_barcode_search.barcode", WebsiteSaleBarcode);
