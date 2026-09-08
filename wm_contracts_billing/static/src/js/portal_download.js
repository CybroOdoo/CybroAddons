/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PortalPDFDownload = publicWidget.Widget.extend({
    selector: '.js_download_pdf',
    events: {
        'click': '_onClickDownload',
    },

    _onClickDownload: function (ev) {
        ev.preventDefault();
        const url = this.el.getAttribute('href');
        if (!url) return;

        // Generate a unique token for this download request
        const token = Date.now().toString();

        // Show the Odoo-themed loader overlay on the current tab
        this._showLoading();

        // Start checking for the response cookie that Odoo sets when sending the file
        let attempts = 0;
        const checkTimer = setInterval(() => {
            const cookieVal = this._getCookie('fileDownloadToken');
            attempts++;
            if (cookieVal === token || attempts > 120) { // Timeout after 60 seconds (120 * 500ms)
                clearInterval(checkTimer);
                this._eraseCookie('fileDownloadToken');
                this._hideLoading();
            }
        }, 500);

        // Trigger the native browser download by navigating to the PDF URL with the token
        const separator = url.indexOf('?') !== -1 ? '&' : '?';
        window.location.href = url + separator + 'downloadToken=' + token;
    },

    _getCookie: function (name) {
        const parts = `; ${document.cookie}`.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    },

    _eraseCookie: function (name) {
        document.cookie = name + '=; Max-Age=-99999999; path=/';
    },

    _showLoading: function () {
        let loader = document.getElementById('pdf_download_loader');
        if (!loader) {
            loader = document.createElement('div');
            loader.id = 'pdf_download_loader';
            loader.className = 'pdf-download-loader-overlay';
            loader.innerHTML = `
                <div class="pdf-download-loader-card">
                    <div class="pdf-download-spinner"></div>
                    <div class="pdf-download-loader-text">Generating PDF...</div>
                    <div class="pdf-download-loader-subtext">Please wait while we prepare your document.</div>
                </div>
            `;
            document.body.appendChild(loader);
        }
        // Force reflow
        loader.offsetHeight;
        loader.classList.add('active');
    },

    _hideLoading: function () {
        const loader = document.getElementById('pdf_download_loader');
        if (loader) {
            loader.classList.remove('active');
        }
    }
});

