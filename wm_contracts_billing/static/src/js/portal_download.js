import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

const DOWNLOAD_TIMEOUT_ATTEMPTS = 120; // 60 seconds (120 * 500ms)

export class PortalPDFDownload extends Interaction {
    static selector = ".js_download_pdf";
    dynamicContent = {
        _root: { "t-on-click.prevent": this.onClickDownload },
    };

    onClickDownload() {
        const url = this.el.getAttribute("href");
        if (!url) {
            return;
        }
        // Unique token for this download request
        const token = Date.now().toString();
        this.showLoading();

        // Wait for the cookie Odoo sets when it sends the file
        let attempts = 0;
        const timer = setInterval(() => {
            attempts++;
            if (this.getCookie("fileDownloadToken") === token || attempts > DOWNLOAD_TIMEOUT_ATTEMPTS) {
                clearInterval(timer);
                this.eraseCookie("fileDownloadToken");
                this.hideLoading();
            }
        }, 500);
        this.registerCleanup(() => clearInterval(timer));

        // Native browser download with the token appended
        const separator = url.includes("?") ? "&" : "?";
        window.location.href = `${url}${separator}downloadToken=${token}`;
    }

    getCookie(name) {
        const parts = `; ${document.cookie}`.split(`; ${name}=`);
        return parts.length === 2 ? parts.pop().split(";").shift() : null;
    }

    eraseCookie(name) {
        document.cookie = `${name}=; Max-Age=-99999999; path=/`;
    }

    showLoading() {
        let loader = document.getElementById("pdf_download_loader");
        if (!loader) {
            loader = document.createElement("div");
            loader.id = "pdf_download_loader";
            loader.className = "pdf-download-loader-overlay";
            loader.innerHTML = `
                <div class="pdf-download-loader-card">
                    <div class="pdf-download-spinner"></div>
                    <div class="pdf-download-loader-text"></div>
                    <div class="pdf-download-loader-subtext"></div>
                </div>
            `;
            loader.querySelector(".pdf-download-loader-text").textContent = _t("Generating PDF...");
            loader.querySelector(".pdf-download-loader-subtext").textContent = _t(
                "Please wait while we prepare your document."
            );
            document.body.appendChild(loader);
        }
        // Force a reflow so the transition runs
        loader.offsetHeight;
        loader.classList.add("active");
    }

    hideLoading() {
        document.getElementById("pdf_download_loader")?.classList.remove("active");
    }
}

registry.category("public.interactions").add("wm_contracts_billing.portal_pdf_download", PortalPDFDownload);
