/** @odoo-module **/
import { NavBar } from '@web/webclient/navbar/navbar';
import { patch } from "@web/core/utils/patch";
import { onMounted, onWillUnmount, signal } from "@odoo/owl";

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.openElement = signal.ref();
        this.closeElement = signal.ref();
        this.topHeading = signal.ref();
        this.mainNavBar = signal.ref();
        this.sidebarLinks = signal.ref();
        this.sidebarPanel = signal.ref();
        const sidebarLinkHandler = this.handleSidebarLinkClick.bind(this);
        const openSidebarHandler = (ev) => {
            if (ev) ev.preventDefault();
            this.openSidebar();
        };
        const closeSidebarHandler = (ev) => {
            if (ev) ev.preventDefault();
            this.closeSidebar();
        };

        onMounted(() => {
            // Auto open sidebar on mount
            this.openSidebar();

            const openSidebarElement = this.openElement() || document.getElementById('openSidebar');
            const closeSidebarElement = this.closeElement() || document.getElementById('closeSidebar');
            const sidebarLinksEl = this.sidebarLinks() || document.querySelector('.sidebar_menu');
            const sidebarLinkElements = sidebarLinksEl ? sidebarLinksEl.children : null;

            if (sidebarLinkElements) {
                Array.from(sidebarLinkElements).forEach(link => {
                    link.addEventListener('click', sidebarLinkHandler);
                });
            }
            if (openSidebarElement) {
                openSidebarElement.addEventListener('click', openSidebarHandler);
            }
            if (closeSidebarElement) {
                closeSidebarElement.addEventListener('click', closeSidebarHandler);
            }
            const panelCloseBtn = document.querySelector('.sidebar_close #closeSidebar');
            if (panelCloseBtn) {
                panelCloseBtn.addEventListener('click', closeSidebarHandler);
            }
        });

        onWillUnmount(() => {
            const openSidebarElement = this.openElement() || document.getElementById('openSidebar');
            const closeSidebarElement = this.closeElement() || document.getElementById('closeSidebar');
            const sidebarLinksEl = this.sidebarLinks() || document.querySelector('.sidebar_menu');
            const sidebarLinkElements = sidebarLinksEl ? sidebarLinksEl.children : null;
            if (openSidebarElement) {
                openSidebarElement.removeEventListener('click', openSidebarHandler);
            }
            if (closeSidebarElement) {
                closeSidebarElement.removeEventListener('click', closeSidebarHandler);
            }
            if (sidebarLinkElements) {
                Array.from(sidebarLinkElements).forEach(link => {
                    link.removeEventListener('click', sidebarLinkHandler);
                });
            }
            const panelCloseBtn = document.querySelector('.sidebar_close #closeSidebar');
            if (panelCloseBtn) {
                panelCloseBtn.removeEventListener('click', closeSidebarHandler);
            }
        });
    },

    openSidebar() {
        const actionManager = document.querySelector('.o_action_manager') || document.querySelector('.o_web_client > *:nth-child(2)');
        if (actionManager) {
            actionManager.style.marginLeft = '200px';
            actionManager.style.transition = 'all .1s linear';
        }
        const sidebarPanel = this.sidebarPanel ? this.sidebarPanel() : document.getElementById('sidebar_panel');
        if (sidebarPanel) {
            sidebarPanel.style.display = 'block';
            sidebarPanel.style.left = '0px';
            sidebarPanel.style.top = '0px';
            sidebarPanel.style.height = '100vh';
            sidebarPanel.style.width = '200px';
            sidebarPanel.style.position = 'fixed';
            sidebarPanel.style.zIndex = '9999';
            sidebarPanel.style.backgroundColor = '#2a3042';
        }
        const openSidebarElement = this.openElement() || document.getElementById('openSidebar');
        const closeSidebarElement = this.closeElement() || document.getElementById('closeSidebar');
        if (openSidebarElement) openSidebarElement.style.display = 'none';
        if (closeSidebarElement) closeSidebarElement.style.display = 'block';
        const topHeadingEl = this.topHeading() || document.querySelector('.top_heading');
        if (topHeadingEl && topHeadingEl.nodeType === Node.ELEMENT_NODE) {
            topHeadingEl.style.marginLeft = '200px';
            topHeadingEl.style.transition = 'all .1s linear';
            topHeadingEl.style.width = 'auto';
        }
    },

    closeSidebar() {
        const actionManager = document.querySelector('.o_action_manager') || document.querySelector('.o_web_client > *:nth-child(2)');
        if (actionManager) {
            actionManager.style.marginLeft = '0px';
            actionManager.style.transition = 'all .1s linear';
        }
        const sidebarPanel = this.sidebarPanel ? this.sidebarPanel() : document.getElementById('sidebar_panel');
        if (sidebarPanel) {
            sidebarPanel.style.display = 'none';
        }
        const openSidebarElement = this.openElement() || document.getElementById('openSidebar');
        const closeSidebarElement = this.closeElement() || document.getElementById('closeSidebar');
        if (openSidebarElement) openSidebarElement.style.display = 'block';
        if (closeSidebarElement) closeSidebarElement.style.display = 'none';
        const topHeadingEl = this.topHeading() || document.querySelector('.top_heading');
        if (topHeadingEl && topHeadingEl.nodeType === Node.ELEMENT_NODE) {
            topHeadingEl.style.marginLeft = '0px';
            topHeadingEl.style.width = '100%';
        }
    },

    handleSidebarLinkClick(event) {
        const closeSidebarElement = this.closeElement() || document.getElementById('closeSidebar');
        if (closeSidebarElement) closeSidebarElement.style.display = 'none';

        const topHeadingEl = this.topHeading() || document.querySelector('.top_heading');
        if (topHeadingEl && topHeadingEl.nodeType === Node.ELEMENT_NODE) {
            topHeadingEl.style.marginLeft = '0px';
            topHeadingEl.style.width = '100%';
        }
        const li = event.currentTarget;
        if (!li) return;
        const a = li.firstElementChild;
        if (a) {
            const id = a.getAttribute('data-id');
            const header = document.querySelector('header');
            if (header && id) {
                header.className = id;
            }
        }

        const sidebarLinksEl = this.sidebarLinks() || document.querySelector('.sidebar_menu');
        if (sidebarLinksEl) {
            Array.from(sidebarLinksEl.children).forEach(item => {
                if (item.firstElementChild) {
                    item.firstElementChild.classList.remove('active');
                }
            });
        }
        if (a) {
            a.classList.add('active');
        }
        this.closeSidebar();
    }
});