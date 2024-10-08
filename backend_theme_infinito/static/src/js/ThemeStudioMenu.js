/** @odoo-module **/
import {ThemeStudioWidget} from "./ThemeStudioWidget";
import {jsonrpc} from "@web/core/network/rpc_service";

export class ThemeStudioMenu extends ThemeStudioWidget {
    static template = "backend_theme_infinito.ThemeStudioMenu"

    constructor(parent, action) {
        super(...arguments);
        this.action = action;
        this.parent = parent;
        this.editMode = parent.editMode;
        this.menus = [{
            name: 'Views',
            children: [{
                'name': 'Tree/List',
                'selector': 'tree',
            },
                {
                    'name': 'Form',
                    'selector': 'form',
                },
                {
                    'name': 'Kanban',
                    'selector': 'kanban',
                },
                {
                    'name': 'Control Panel',
                    'selector': 'control_panel',
                }],
        }, {
            name: 'UI Elements',
            children: [{
                'name': 'Button',
                'selector': 'button',
            },
                {
                    'name': 'Progress Bar',
                    'selector': 'progress_bar',
                },
                {
                    'name': 'Tab',
                    'selector': 'tab',
                },
                {
                    'name': 'Input',
                    'selector': 'input',
                },
                {
                    'name': 'Search',
                    'selector': 'search',
                },
                {
                    'name': 'Misc',
                    'selector': 'misc',
                },],
        }
        ];
    }

    /**
     * Handles the click event to close the theme studio.
     * @param {Event} ev - The event object representing the click event.
     */
    _onThemeStudioClose(ev) {
        ev.preventDefault();
        window.location.href = '/web'
    }

    /**
     * Handles the click event to toggle the sidebar in the theme studio.
     * @param {Event} ev - The event object representing the click event.
     */
    _onThemeStudioToggleSidebar(ev) {
        ev.currentTarget.classList.toggle('open');
        ev.preventDefault();
        this.parent._onToggleSidebar();
    }

    /**
     * Handles the click event for button actions.
     * @param {Event} ev - The event object representing the click event.
     */
    _onButtonClick(ev) {
        ev.preventDefault();
        var mode = ev.currentTarget.id;
        if (mode) {
            this.parent.editMode = mode;
            this.parent.render();
            this.editMode = mode;
            var sidebar = this.parent.sidebar;
            if (sidebar) {
                sidebar._Close();
                sidebar.destroy();
            }
            this.saveData();
        } else {
            var mode = ev.currentTarget.dataset.other;
            this.parent.colors();
        }
    }

    /**
     * Handles the click event to reset settings to default.
     * @param {Event} ev - The event object representing the click event.
     */
    async _onResetClick(ev) {
        await jsonRpc('/theme_studio/reset_to_default', 'call', {});
        await this.setAssets();
        location.reload();
    }

    /**
     * Sets assets for debugging purposes.
     */
    setAssets() {
        location.search = "?debug=assets";
    }

    /**
     * Saves data to the local storage.
     */
    saveData() {
        this._super.apply(this, arguments);
        this.localStorage.setItem('editMode', this.editMode);
    }
}
