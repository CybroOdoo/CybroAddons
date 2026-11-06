/**
 * website_purchase_limit — Pure vanilla JS (no module dependencies).
 * Displays a simple default Odoo error popup when purchase limit is not met.
 */
(function () {
    'use strict';

    /**
     * Injects popup CSS into <head> once per page load.
     */
    function injectStyles() {
        if (document.getElementById('pl_popup_styles')) { return; }
        var style = document.createElement('style');
        style.id = 'pl_popup_styles';
        style.textContent = [
            '#popup_error_message {',
            '  position: fixed;',
            '  top: 0; left: 0; right: 0; bottom: 0;',
            '  z-index: 10500;',
            '  background: rgba(0, 0, 0, 0.4);',
            '  display: flex;',
            '  justify-content: center;',
            '  align-items: flex-start;',
            '  padding-top: 60px;',
            '}',
            '#pl_popup_card {',
            '  background: #ffffff;',
            '  border: 1px solid rgba(0, 0, 0, 0.2);',
            '  border-radius: 6px;',
            '  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);',
            '  width: 100%;',
            '  max-width: 480px;',
            '  margin: 0 16px;',
            '  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;',
            '}',
            '.pl-header {',
            '  display: flex;',
            '  align-items: center;',
            '  justify-content: space-between;',
            '  padding: 14px 20px;',
            '  border-bottom: 1px solid #e9ecef;',
            '}',
            '.pl-title {',
            '  font-size: 15px;',
            '  font-weight: 600;',
            '  color: #212529;',
            '  margin: 0;',
            '}',
            '.pl-close-x {',
            '  background: transparent;',
            '  border: none;',
            '  font-size: 18px;',
            '  line-height: 1;',
            '  color: #6c757d;',
            '  cursor: pointer;',
            '  padding: 0 4px;',
            '}',
            '.pl-close-x:hover {',
            '  color: #000;',
            '}',
            '.pl-body {',
            '  padding: 20px;',
            '  font-size: 14px;',
            '  color: #212529;',
            '  line-height: 1.5;',
            '}',
            '.pl-body b {',
            '  font-weight: 700;',
            '}'
        ].join('\n');
        document.head.appendChild(style);
    }

    /**
     * Show the default Odoo style simple error popup.
     * @param {number|string} limit - The minimum required order amount.
     */
    function showPopup(limit) {
        injectStyles();

        var old = document.getElementById('popup_error_message');
        if (old) { old.remove(); }

        var numLimit = parseFloat(limit || 0);
        var limitDisplay = (numLimit % 1 === 0) ? parseInt(numLimit, 10) : numLimit;

        var overlay = document.createElement('div');
        overlay.id = 'popup_error_message';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.innerHTML =
            '<div id="pl_popup_card">' +
            '<div class="pl-header">' +
            '<h5 class="pl-title">The purchase amount did not meet the limit!</h5>' +
            '<button class="pl-close-x" aria-label="Close" title="Close">&#10005;</button>' +
            '</div>' +
            '<div class="pl-body">' +
            'The purchase amount must be at least <b>' + limitDisplay + '</b>' +
            '</div>' +
            '</div>';

        document.body.appendChild(overlay);

        function close() { overlay.remove(); }

        overlay.querySelector('.pl-close-x').addEventListener('click', close);
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) { close(); }
        });

        function onKey(e) {
            if (e.key === 'Escape') {
                close();
                document.removeEventListener('keydown', onKey);
            }
        }
        document.addEventListener('keydown', onKey);
    }

    /**
     * Main entry point.
     * 1. Shows popup if server redirected back with purchase_limit_error in URL.
     * 2. Intercepts checkout button clicks when the cart total is below limit.
     */
    function init() {
        // Case 1 — server-side redirect back to cart: show popup from URL params
        var params = new URLSearchParams(window.location.search);
        if (params.get('purchase_limit_error')) {
            var limit = parseFloat(params.get('limit') || '0');
            showPopup(limit);
            // Clean the URL so the popup won't reappear on page refresh
            window.history.replaceState(null, '', window.location.pathname);
        }

        // Case 2 — client-side: intercept checkout button click via event delegation
        document.addEventListener('click', function (e) {
            var btn = e.target.closest('a[name="website_sale_main_button"]');
            if (!btn) { return; }
            var limitEl = document.getElementById('website_purchase_limit_value');
            if (limitEl) {
                e.preventDefault();
                var clickLimit = parseFloat(limitEl.getAttribute('limit'));
                showPopup(clickLimit);
            }
        });
    }

    // Wait for DOM before initialising
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

}());

