/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import { rpc } from '@web/core/network/rpc';

publicWidget.registry.LiveloPropertyList = publicWidget.Widget.extend({
    selector: '.s_properties_list',
    disabledInEditableMode: true,

    start: async function () {
        await this._super(...arguments);
        let container = this.el.querySelector('.s_properties_list_container');
        if (!container) {
            // Support previously dropped snippet instances without s_properties_list_container
            const oldRow = this.el.querySelector('.container > .row');
            if (oldRow) {
                container = document.createElement('div');
                container.className = 's_properties_list_container o_not_editable';
                container.setAttribute('contenteditable', 'false');
                oldRow.parentNode.insertBefore(container, oldRow);
                oldRow.remove();
            }
        }
        if (!container) {
            this._setupTabs();
            return;
        }

        // Save original HTML to restore when entering Edit Mode
        this.originalHTML = container.innerHTML;

        // If in editable mode and container already has content, just wire up tabs
        if (this.editableMode && container.children.length > 0) {
            this._setupTabs();
            return;
        }

        try {
            const data = await rpc('/theme_livelo/get_featured_properties', {});
            if (data && data.html) {
                container.innerHTML = data.html;
                this._setupTabs();
            }
        } catch (err) {
            console.warn('LiveloPropertyList: failed to fetch dynamic properties:', err);
            this._setupTabs();
        }
    },

    destroy: function () {
        const container = this.el.querySelector('.s_properties_list_container');
        if (container && this.originalHTML) {
            // Restore the placeholder before entering Edit Mode or saving
            container.innerHTML = this.originalHTML;
        }
        this._super(...arguments);
    },

    _setupTabs: function () {
        const instanceId = 'prop_' + Math.random().toString(36).substring(2, 9);
        const navLinks = this.el.querySelectorAll('.s_property_nav_tabs a, .nav-tabs a[data-bs-toggle="tab"]');
        const panes = this.el.querySelectorAll('.s_property_tab_content > .tab-pane, .tab-content > .tab-pane');

        if (!navLinks.length || !panes.length) {
            return;
        }

        // Assign unique IDs to panes and link nav items by index
        panes.forEach((pane, idx) => {
            const newId = `${instanceId}_tab_${idx}`;
            pane.setAttribute('id', newId);
        });

        navLinks.forEach((link, idx) => {
            const targetPane = panes[idx];
            if (targetPane) {
                const newTarget = '#' + targetPane.getAttribute('id');
                link.setAttribute('href', newTarget);
                link.setAttribute('data-bs-target', newTarget);
            }
            // Remove data-bs-toggle to prevent Bootstrap Tab plugin from
            // conflicting with our manual click handler
            link.removeAttribute('data-bs-toggle');
            link.addEventListener('click', (e) => {
                e.preventDefault();

                navLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');

                panes.forEach(p => {
                    p.classList.remove('show', 'active');
                });

                if (targetPane) {
                    targetPane.classList.add('show', 'active');
                }
            });
        });
    },
});

export default publicWidget.registry.LiveloPropertyList;
