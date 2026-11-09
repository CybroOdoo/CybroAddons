/** @odoo-module **/
import { Component, onWillUnmount, proxy, signal } from "@odoo/owl";


import {session} from "@web/session";

import {rpc} from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

export class Counter extends Component {
    panelRef = signal.ref();
    get canManageTheme() {
        return Boolean(session.infinitoCanManageTheme);
    }

    static template = "backend_theme_infinito.theme_editor_sidebar_advanced";

    /**
     * Setup function to initialize the state and perform actions on component mount.
     */
    setup() {
        this.notification = useService("notification");
        this.advancedPanel = useService("infinito_advanced_panel");
        onWillUnmount(() => {
            clearTimeout(this._loaderTimer);
            this._loaderPreview?.remove();
        });
        // Keep form values in Owl state.
        this.state = proxy({
            // Define loaders array with default loader options
            loaders: ['default', 'ring', 'rotating', 'blinking', 'bounce'],
            loader: "",
            settings: {
                userEdit: Boolean(session.userEdit),
                sidebar: Boolean(session.sidebar),
                sidebarIcon: Boolean(session.sidebarIcon),
                sidebarName: Boolean(session.sidebarName),
                sidebarCompany: Boolean(session.sidebarCompany),
                sidebarUser: Boolean(session.sidebarUser),
                fullscreen: Boolean(session.fullscreen),
                recentApps: Boolean(session.recentApps),
                fullScreenApp: Boolean(session.fullScreenApp),
                infinitoDark: Boolean(session.infinitoDark),
                infinitoBookmark: Boolean(session.infinitoBookmark),
                infinitoRtl: Boolean(session.infinitoRtl),
                loaderClass: session.loaderClass || "default",
            },
            mode: session.infinitoDarkMode || "all",
            type: ['user', 'global'],
            fontData: null,
        })
        this.darkStart = session.infinitoDarkStart || '19:00';
        this.darkEnd = session.infinitoDarkEnd || '5:00';
        this.darkStartFloat = this.timeToFloat(this.darkStart);
        this.darkEndFloat = this.timeToFloat(this.darkEnd);
    }


    /** Save the reactive editor settings and refresh the backend. */
    async _SaveChanges() {
        const isUserEdit = this.state.settings.userEdit;
        const vals = {
            ...this.state.settings,
            infinitoDarkMode: this.state.mode,
            infinitoDarkStart: this.darkStartFloat,
            infinitoDarkEnd: this.darkEndFloat,
        };

        // Enforce logic
        if (vals.fullScreenApp && vals.sidebar) {
            vals.sidebar = false;
            this.state.settings.sidebar = false;
        }
        // Enabling Full Screen App Menu above force-disables Sidebar. If the
        // user later turns Full Screen App Menu back off without touching
        // Sidebar themselves, restore it — otherwise both end up disabled and
        // the navbar silently falls back to the plain, unstyled default Odoo
        // apps dropdown instead of either custom layout.
        if (session.fullScreenApp && !vals.fullScreenApp && !vals.sidebar) {
            vals.sidebar = true;
            this.state.settings.sidebar = true;
        }
        if (!vals.sidebarIcon && !vals.sidebarName && vals.sidebar) {
            vals.sidebar = false;
            this.state.settings.sidebar = false;
        }

        try {
            let result;
            if (isUserEdit && !this.canManageTheme) {
                result = await rpc('/theme_studio/set_advanced_data_user', {
                    args: [{vals}]
                });
            } else {
                result = await rpc('/theme_studio/set_advanced_data', {
                    args: [{vals}]
                });
            }

            if (result) {
                // Update session
                Object.assign(session, {
                    userEdit: vals.userEdit,
                    sidebar: vals.sidebar,
                    sidebarIcon: vals.sidebarIcon,
                    sidebarIco: vals.sidebarIcon,
                    sidebarName: vals.sidebarName,
                    fullscreen: vals.fullscreen,
                    infinitoRtl: vals.infinitoRtl,
                    sidebarCompany: vals.sidebarCompany,
                    sidebarUser: vals.sidebarUser,
                    recentApps: vals.recentApps,
                    fullScreenApp: vals.fullScreenApp,
                    infinitoBookmark: vals.infinitoBookmark,
                    infinitoDark: vals.infinitoDark,
                    infinitoDarkMode: vals.infinitoDarkMode,
                    infinitoDarkStart: this.darkStart,
                    infinitoDarkEnd: this.darkEnd,
                    loaderClass: vals.loaderClass,
                });

                window.location.reload();
            }
        } catch {
            this.notification.add(_t("Could not save theme settings. Please try again."), {
                type: "danger",
            });
        }
    }

    /**
     * Discard unsaved form values and close the mounted panel.
     */
    _Close_changes() {
        this.advancedPanel.close();
    }

    /**
     * Handles the change event when the loader selection is modified.
     * @param {Event} ev - The event object representing the change event.
     */
    onSettingChange(name, ev) {
        this.state.settings[name] = ev.target.checked;
    }

    onLoaderChange(ev) {
        this.state.settings.loaderClass = ev.target.value;
        this._loaderPreview?.remove();
        clearTimeout(this._loaderTimer);
        const content = document.createElement('div');
        content.className = 'o_blockUI fixed-top d-flex justify-content-center align-items-center flex-column vh-100';
        const spinner = document.createElement('div');
        spinner.className = 'o_spinner mb-4';
        const value = ev.target.value;
        const loader = document.createElement(value === 'default' ? 'img' : 'span');
        if (value === 'default') {
            loader.src = '/web/static/img/spin.svg';
            loader.alt = _t('Loading...');
        } else {
            loader.className = this.state.loaders.includes(value) ? value : '';
        }
        spinner.append(loader);
        const message = document.createElement('div');
        message.className = 'o_message text-center px-4';
        message.textContent = _t('Loading...');
        content.append(spinner, message);
        this._loaderPreview = content;
        document.body.append(content);
        this._loaderTimer = setTimeout(() => content.remove(), 3000);
    }

    /**
     * Handles the change event when the time selection is modified.
     * @param {Event} ev - The event object representing the change event.
     */
    onChangeTime(ev) {
        // Convert the selected time to a float value and assign it to darkStartFloat
        this.darkStartFloat = this.timeToFloat(ev.target.value);
        this.darkStart = ev.target.value;
    }

    /**
     * Handles the change event when the second time selection is modified.
     * @param {Event} ev - The event object representing the change event.
     */
    onChangeTime2(ev) {
        // Convert the selected time to a float value and assign it to darkEndFloat
        this.darkEndFloat = this.timeToFloat(ev.target.value);
        this.darkEnd = ev.target.value;
    }

    /**
     * Handles the change event when the dark mode option is modified.
     * @param {Event} ev - The event object representing the change event.
     */
    _OnChangeDark(ev) {
        this.showDarkOptions(ev.target.checked);

    }

    /**
     * Displays or hides dark mode options based on the toggle status.
     * @param {boolean} toggle - The toggle status indicating whether to show or hide the dark mode options.
     */
    showDarkOptions(toggle) {
        this.state.settings.infinitoDark = toggle;
    }

    onLayoutChange(ev) {
        const sidebar = ev.target.id === 'sidebarToggler';
        this.state.settings.sidebar = sidebar ? ev.target.checked : !ev.target.checked;
        this.state.settings.fullScreenApp = !this.state.settings.sidebar;
    }

    /**
     * Handles the change event when the dark mode setting is modified.
     * @param {Event} ev - The event object representing the change event.
     */
    onChangeDarkMode(ev) {
        const target = ev.target.closest('a');
        if (target) {
            this.state.mode = target.dataset.mode;
            // Update UI for new mode
            this.showDarkOptions(this.state.settings.infinitoDark);
            if (this.state.mode === 'auto') {
                this.darkStartFloat = 19.0;
                this.darkEndFloat = 5.0;
                this.darkStart = '19:00';
                this.darkEnd = '05:00';
            }
        }
    }

    /**
     * Converts time string (HH:MM) to float (HH.MM).
     * @param {string} time - Time in HH:MM format.
     * @returns {number} Time as float.
     */
    timeToFloat(time) {
        const [hours, minutes] = time.split(':').map(Number);
        return hours + (minutes / 60);
    }


    /**
     * Handles click on schedule input to show time picker.
     * @param {Event} ev - The event object.
     */
    onClickSchedule(ev) {
        const input = ev.target.closest('.input-group')?.querySelector('input[type="time"]');
        if (input?.showPicker) input.showPicker();
    }
}

export class EditorMenu extends Component {
    static template = "backend_theme_infinito.sidebar_simple_editor";
    static components = {Counter};
}
