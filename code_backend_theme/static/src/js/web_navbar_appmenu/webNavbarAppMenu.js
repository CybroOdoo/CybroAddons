/** @odoo-module **/

import { NavBar } from '@web/webclient/navbar/navbar';
import { patch } from "@web/core/utils/patch";

import {
    Component,
    onWillDestroy,
    useExternalListener,
    onMounted,
    useRef,
    onWillUnmount,
} from "@odoo/owl";

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.openElement = useRef("openSidebar");
        this.closeElement = useRef("closeSidebar");
        this.topHeading = useRef("top_heading");
        this.mainNavBar = useRef("o_main_navbar");
        this.sidebarLinks = useRef("sidebarLinks");
        const sidebarLinkHandler = this.handleSidebarLinkClick.bind(this);
        const openSidebarHandler = this.openSidebar.bind(this);
        const closeSidebarHandler = this.closeSidebar.bind(this);
        onMounted(() => {
            const openSidebarElement = this.openElement.el
            const closeSidebarElement = this.closeElement.el
            const sidebarLinkElements = this.sidebarLinks.el.children;
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
        });

        onWillUnmount(() => {
            const openSidebarElement = this.openElement.el
            const closeSidebarElement = this.closeElement.el
            const sidebarLinkElements = this.sidebarLinks.el.children;
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
        });
    },

    openSidebar() {
        this.root.el.nextElementSibling.style.marginLeft = '200px';
        this.root.el.nextElementSibling.style.transition = 'all .1s linear';
        const openSidebarElement = this.openElement.el
        const closeSidebarElement = this.closeElement.el
        if (openSidebarElement) openSidebarElement.style.display = 'none';
        if (closeSidebarElement) closeSidebarElement.style.display = 'block';
        if (this.root.el.lastChild && this.root.el.lastChild.nodeType === Node.ELEMENT_NODE) {
            this.root.el.lastChild.style.display = 'block';
        }
        if (this.topHeading.el && this.topHeading.el.nodeType === Node.ELEMENT_NODE) {
          this.topHeading.el.style.marginLeft = '200px';
          this.topHeading.el.style.transition = 'all .1s linear';
          this.topHeading.el.style.width = 'auto';
        }
    },

    closeSidebar() {
        console.log('Sidebar closed', this.topHeading);
        this.root.el.nextElementSibling.style.marginLeft = '0px';
        this.root.el.nextElementSibling.style.transition = 'all .1s linear';
        const openSidebarElement = this.openElement.el
        const closeSidebarElement = this.closeElement.el
        if (openSidebarElement) openSidebarElement.style.display = 'block';
        if (closeSidebarElement) closeSidebarElement.style.display = 'none';
        if (this.root.el.lastChild && this.root.el.lastChild.nodeType === Node.ELEMENT_NODE) {
            this.root.el.lastChild.style.display = 'none';
        }
        if (this.topHeading.el && this.topHeading.el.nodeType === Node.ELEMENT_NODE) {
          this.topHeading.el.style.marginLeft = '0px';
          this.topHeading.el.style.width = '100%';
        }
    },

    handleSidebarLinkClick(event) {
        const closeSidebarElement = this.closeElement.el
        if (closeSidebarElement) closeSidebarElement.style.display = 'none';
        if (this.topHeading.el && this.topHeading.el.nodeType === Node.ELEMENT_NODE) {
          this.topHeading.el.style.marginLeft = '0px';
        }
        if (this.topHeading.el && this.topHeading.el.nodeType === Node.ELEMENT_NODE) {
          this.topHeading.el.style.marginLeft = '0px';
          this.topHeading.el.style.width = '100%';
        }
        const li = event.currentTarget;
        const a = li.firstElementChild;
        const id = a.getAttribute('data-id');
        document.querySelector('header').className = id;
        Array.from(this.sidebarLinks.el.children).forEach(li => {
            li.firstElementChild.classList.remove('active');
        });
        a.classList.add('active');
        this.closeSidebar();
    }
});