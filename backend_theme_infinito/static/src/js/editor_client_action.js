/** @odoo-module **/
import {Component, useState} from "@odoo/owl";
import {EditorMenu} from "./editor_menu"
import {ThemeEditorSidebar} from "./theme_editor_sidebar"
import {rpc} from "@web/core/network/rpc";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

const {onMounted, onPatched, mount, useEnv} = owl

/**
 * EditorClientAction class handles client actions for theme editing.
 */
export class EditorClientAction extends Component {
    /**
     * Sets up the initial state and environment for the EditorClientAction component.
     */
    setup() {
        super.setup();
        this.env = useEnv();
        this.dialog = useService("dialog");
        this._mountedSidebar = null;
        this._autoSelectTimer = null;
        var navbar = document.querySelector(".o_main_navbar")
        if (navbar) {
            navbar.style.display = "none";
        }
        this._closeMainSidebar();
        this.state = useState({
            menus: false,
            viewType: 'tree',
            sidebarOpen: false,
        })
        this.state.menus = [{
            id: 1,
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
            id: 2,
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


        onMounted(() => {
            this._syncMainOffsetForPresetSidebar();
            this._closeMainSidebar();
        });
        if (onPatched) {
            onPatched(() => this._syncMainOffsetForPresetSidebar());
        }
    }

    _closeMainSidebar() {
        const closeBtn = document.getElementById("closeSidebar");
        const openBtn = document.getElementById("openSidebar");
        const sidebarPanel = document.getElementById("sidebar_panel");

        if (closeBtn) closeBtn.style.display = "none";
        if (openBtn) openBtn.style.display = "block";
        if (sidebarPanel) sidebarPanel.style.display = "none";

        const actionManager = document.querySelector(".o_action_manager");
        const topHead = document.querySelector(".top_heading");

        if (actionManager) {
            const actionManagerId = actionManager.dataset.id;
            if (actionManagerId) {
                document.querySelectorAll("div").forEach(div => div.classList.remove(actionManagerId));
            }
            actionManager.classList.remove("sidebar_margin");
        }

        if (topHead) {
            const topHeadId = topHead.dataset.id;
            if (topHeadId) {
                document.querySelectorAll("div").forEach(div => div.classList.remove(topHeadId));
            }
            topHead.classList.remove("sidebar_margin");
        }
    }

    _closePresetSidebar() {
        try {
            if (this._mountedSidebar?.destroy) {
                this._mountedSidebar.destroy();
            }
        } catch {
        }
        this._mountedSidebar = null;
        const existingSidebar = document.getElementById("theme_editor_sidebar_preset");
        if (existingSidebar) existingSidebar.remove();
        this._syncMainOffsetForPresetSidebar();
    }

    _autoSelectFirstPreviewItem(retries = 8) {
        if (this._autoSelectTimer) {
            clearTimeout(this._autoSelectTimer);
            this._autoSelectTimer = null;
        }
        const pick = () => {
            // Prefer leaf items that have both name and class (those are editable/stylable targets).
            const el =
                document.querySelector(".preview_area .item[data-name][data-class]") ||
                document.querySelector(".preview_area .item[data-name]") ||
                document.querySelector(".preview_area .item");
            if (el) {
                el.dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true}));
                return true;
            }
            return false;
        };
        if (pick()) return;
        if (retries <= 0) return;
        this._autoSelectTimer = setTimeout(() => this._autoSelectFirstPreviewItem(retries - 1), 60);
    }

    _syncMainOffsetForPresetSidebar() {
        const main = document.querySelector(".marg_main");
        if (!main) return;

        const presetSidebar = document.getElementById("theme_editor_sidebar_preset");
        if (!presetSidebar) {
            // Don't fight other sidebars (hamburger/simple editor).
            const simpleSidebar = document.querySelector(".sidebar_simple_editor");
            if (simpleSidebar || this.state.sidebarOpen) {
                return;
            }
            main.style.marginLeft = "0px";
            main.style.width = "100%";
            return;
        }

        const width = Math.ceil(presetSidebar.getBoundingClientRect().width || 330);
        main.style.marginLeft = `${width}px`;
        main.style.width = `calc(100% - ${width}px)`;
    }

    /**
     * Handles button click event to switch between view types.
     * @param {Event} ev - The click event object.
     */
    _onButtonClick(ev) {
        ev.preventDefault();
        const mode = ev.currentTarget.id;


        const hadPresetSidebar = !!document.getElementById("theme_editor_sidebar_preset");
        if (hadPresetSidebar) {
            this._closePresetSidebar();
        }

        if (this.state.sidebarOpen) {
            this._closeSidebar();
        }

        this.state.viewType = mode;
        setTimeout(() => {
            this._syncMainOffsetForPresetSidebar();
            if (hadPresetSidebar) {
                this._autoSelectFirstPreviewItem();
            }
        }, 0);
    }

    _closeSidebar() {
        const main_div = document.querySelector('.marg_main');
        const sidebar = document.querySelector(".sidebar_simple_editor");

        this.state.sidebarOpen = false;

        if (sidebar) {
            sidebar.remove();
        }

        if (main_div) {
            main_div.style.marginLeft = "0";
            main_div.style.width = "100%";
        }

        const hamburger = document.querySelector('.theme_studio_toggle_sidebar');
        if (hamburger) {
            hamburger.classList.remove('open');
        }

        this._syncMainOffsetForPresetSidebar();
    }

    /**
     * Handles item click event in the menu.
     * @param {Event} ev - The click event object.
     */
    onItemClick(ev) {
        try {
            if (this._mountedSidebar?.destroy) {
                this._mountedSidebar.destroy();
            }
        } catch {
            // ignore
        }
        this._mountedSidebar = null;
        const existingSidebar = document.getElementById("theme_editor_sidebar_preset");
        if (existingSidebar) existingSidebar.remove();


        if (this.state.sidebarOpen || document.querySelector(".sidebar_simple_editor")) {
            this._closeSidebar();
        }

        const targetEl = ev.currentTarget;
        const object = {target: targetEl};
        var elem_name = targetEl.dataset.name
        var preset = (ev.target && ev.target.dataset && ev.target.dataset.preset) || targetEl.dataset.preset
        var env = this.env;
        var dialog = this.dialog;
        ev.stopPropagation();
        this.sidebar_pos = document.querySelector('.backend_theme_studio_sidebar .sidebar-here')
        const mounted = mount(ThemeEditorSidebar, document.body, {
            env,
            dialog,
            props: {
                elem_name,
                preset,
                object,
                onClose: () => this._closePresetSidebar(),
            },
        });
        if (mounted && typeof mounted.then === "function") {
            mounted.then((inst) => {
                this._mountedSidebar = inst;
                // Ensure the newly rendered view is shifted correctly.
                this._syncMainOffsetForPresetSidebar();
            });
        } else {
            this._mountedSidebar = mounted;
            // Mount is sync in this build, but defer to be safe.
            setTimeout(() => this._syncMainOffsetForPresetSidebar(), 0);
        }
    }

    /**
     * Handles the event when the theme studio sidebar is closed.
     * @param {Event} ev - The click event object.
     */
    _onThemeStudioClose(ev) {
        ev.preventDefault();
        window.location.href = '/web'
    }

    /**
     * Handles the event when the reset button is clicked to reset to default settings.
     * @param {Event} ev - The click event object.
     */
    _onResetClick(ev) {
        rpc('/theme_studio/reset_to_default', {
            method: 'call',
        });
        this.setAssets();
        location.reload();
    }

    /**
     * Toggles the sidebar visibility.
     * @param {Event} ev - The click event object.
     */
    _onThemeStudioToggleSidebar(ev) {
        ev.currentTarget.classList.toggle('open');
        var main_div = document.querySelector('.marg_main');
        this.state.sidebarOpen = !this.state.sidebarOpen;
        ev.preventDefault();
        if (main_div) {
            if (this.state.sidebarOpen) {
                // Never show the hamburger sidebar and the preset sidebar at the same time.
                // If a preset sidebar is open, close it before mounting the hamburger sidebar.
                if (document.getElementById("theme_editor_sidebar_preset")) {
                    this._closePresetSidebar();
                }
                mount(EditorMenu, document.body);
                main_div.style.marginLeft = "340px";
                main_div.style.width = "calc(100% - 340px)";
            } else {

                main_div.style.marginLeft = "0";
                const side = document.querySelector(".sidebar_simple_editor");
                if (side) side.remove();
                main_div.style.width = "100%";
            }
        }

    }

    /**
     * Sets the assets for the theme editor.
     */
    setAssets() {
        location.search = "?debug=assets";
    }
}

EditorClientAction.template = "backend_theme_infinito.ThemeStudioMenu";

registry.category("actions").add("backend_theme_infinito.editor_client_action", EditorClientAction);
