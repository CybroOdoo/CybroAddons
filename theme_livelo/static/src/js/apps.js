/** @odoo-module **/

import { Component, useState, onMounted, useRef } from '@odoo/owl';
import hljs from 'highlight.js';
// Responsive Navigation Component
export class ResponsiveNav extends Component {
    setup() {
        this.navBar = useRef('navBar');
        this.state = useState({ active: false });
    }
    toggleNavBar(ev) {
        ev.preventDefault();
        this.state.active = !this.state.active;
        this.navBar.el.classList.toggle('active', this.state.active);
    }
}
ResponsiveNav.template = `
<div>
    <button t-on-click="toggleNavBar" id="toggle-nav">Toggle Nav</button>
    <div t-ref="navBar" class="nav-bar">
        <ul>
            <li><a href="home.html">Home</a></li>
            <li><a href="about.html">About</a></li>
            <li><a href="contact.html">Contact</a></li>
        </ul>
    </div>
</div>
`;
// Pseudo Active State Component
export class PseudoActive extends Component {
    setup() {
        onMounted(this.initializeSidenav);
    }
    initializeSidenav() {
        const sidenavLinks = document.querySelectorAll('ul.side-nav a');
        const currentUrl = window.location.pathname.split('/').pop();

        sidenavLinks.forEach((link) => {
            if (link.getAttribute('href') === currentUrl) {
                link.parentElement.classList.add('active');
            }
        });
    }
}
PseudoActive.template = `
<div id="docs">
    <ul class="side-nav">
        <li><a href="home.html">Home</a></li>
        <li><a href="about.html">About</a></li>
        <li><a href="contact.html">Contact</a></li>
    </ul>
</div>
`;
// Highlight.js Initialization
export class HighlightInit extends Component {
    setup() {
        onMounted(() => {
            hljs.configure({ tabReplace: '  ' });
            hljs.initHighlightingOnLoad();
        });
    }
}
HighlightInit.template = `
<div>
    <p>Code Highlighting Initialized</p>
</div>
`;
// Mount the Components
const components = { ResponsiveNav, PseudoActive, HighlightInit };
Object.keys(components).forEach((componentName) => {
    const element = document.querySelector(`#${componentName.toLowerCase()}`);
    if (element) {
        new components[componentName]().mount(element);
    }
});
