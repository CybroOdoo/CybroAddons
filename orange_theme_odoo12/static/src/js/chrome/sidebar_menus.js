/** @odoo-module */
import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this._checkMobileView = this._checkMobileView.bind(this);
        window.addEventListener('resize', this._checkMobileView);
    },

    _checkMobileView() {
        this.state = this.state || {};
        const wasMobile = this.state.isMobile;
        this.state.isMobile = window.innerWidth <= 768;

        if (wasMobile !== this.state.isMobile) {
            this._adjustLayoutForDevice();
        }
    },

    _adjustLayoutForDevice() {
        const sidebarPanel = document.querySelector('#sidebar_panel');
        const actionManager = document.querySelector('.o_action_manager');

        if (!sidebarPanel || !actionManager) return;

        if (this.state.isMobile) {
            sidebarPanel.classList.add('mobile-view');
            actionManager.style.marginLeft = '0';
            sidebarPanel.style.display = 'none';
        } else {
            sidebarPanel.classList.remove('mobile-view');
            if (document.querySelector('#openSidebar .fa')?.classList.contains('opened')) {
                actionManager.style.marginLeft = '320px';
            }
        }
    },

    openSidebar(ev) {
        ev.preventDefault();
        const sidebarPanel = document.querySelector('header #sidebar_panel');
        const actionManager = document.querySelector('body .o_action_manager');
        const icon = ev.target.closest('#openSidebar').querySelector('.fa');

        const isOpening = !icon.classList.contains('opened');

        if (isOpening) {
            sidebarPanel.style.display = 'block';
            icon.classList.add('opened');
            if (!this.state.isMobile) {
                actionManager.style.marginLeft = '320px';
            }
        } else {
            sidebarPanel.style.display = 'none';
            icon.classList.remove('opened');
            actionManager.style.marginLeft = '0';
        }
    },

    _toggleSidebar(show) {
        const sidebarPanel = document.querySelector('header #sidebar_panel');
        const actionManager = document.querySelector('body .o_action_manager');
        const icon = document.querySelector('#openSidebar .fa');

        if (show) {
            sidebarPanel.style.display = 'block';
            icon?.classList.add('opened');
            if (!this.state.isMobile) {
                actionManager.style.marginLeft = '320px';
            }
        } else {
            sidebarPanel.style.display = 'none';
            icon?.classList.remove('opened');
            actionManager.style.marginLeft = '0';
        }
    }
});