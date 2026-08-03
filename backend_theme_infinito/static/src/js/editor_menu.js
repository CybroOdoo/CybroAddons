/** @odoo-module **/
import {Component, useState, xml, onMounted} from "@odoo/owl";
import {session} from "@web/session";
import {TimePicker} from "./timepicker";
import {rpc} from "@web/core/network/rpc";

export class Counter extends Component {
    static template = xml`
      <t t-name="backend_theme_infinito.theme_editor_sidebar_advanced">
            <link rel="stylesheet"
                  href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.5.0/font/bootstrap-icons.css"/>
        <div id="theme_editor_sidebar" class="main_sidebar">
                <div class="sidebar_wrapper">
                    <div class="sidebar_content">
                        <div class="button_properties">
                            <p>
                                <a class="btn btn-primary_style"
                                   data-bs-toggle="collapse" href="#advanced"
                                   role="button"
                                   aria-expanded="false"
                                   aria-controls="advanced">
                                    Advanced
                                </a>
                            </p>
                            <div class="collapse" id="advanced">
                                <div class="card card-body">
                                    <div class="sidebar_left">
                                        <div class="wrapper">
                                            <div class="sub_style">
                                                <div class=" t_settings info-infinito"
                                                     data-bs-toggle="popover"
                                                     data-bs-placement="right"
                                                     data-bs-content="All internal users can edit their Advanced features for themself"
                                                     title=""
                                                     data-bs-original-title="Help">
                                                    User edit
                                                </div>
                                                <label class="switch">
                                                    <input type="checkbox"
                                                           id="userEditToggler"
                                                           checked=""/>
                                                    <span class="slider round"/>
                                                </label>
                                            </div>
                                            <div>
                                                <h6 class="info-infinito"
                                                    data-bs-toggle="popover"
                                                    data-bs-placement="right"
                                                    data-bs-content="All internal users can edit their Advanced features for themself"
                                                    title=""
                                                    data-bs-original-title="Help">
                                                    Loaders
                                                </h6>
                                                <div class="sub_style">
                                                <select class="form-select infinito-form-select" id="loader" t-on-change="onLoaderChange">
                                                <t t-foreach="state.loaders" t-as="load" t-key="load">
                                                    <option t-att-value="load"><t t-esc="load"/></option>
                                                </t>
                                                </select>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="button_properties">
                            <p>
                                <a class="btn btn-primary_style"
                                   data-bs-toggle="collapse" href="#sidebar"
                                   role="button"
                                   aria-expanded="false"
                                   aria-controls="sidebar">
                                    Sidebar
                                </a>
                            </p>
                            <div class="collapse" id="sidebar">
                                <div class="card card-body">
                                    <div class="sidebar_left">
                                        <div class="wrapper">
                                            <div class="sub_style">
                                                <div class=" t_settings info-infinito"
                                                     data-bs-toggle="popover"
                                                     data-bs-placement="right"
                                                     data-bs-content="Enables sidebar apps menu"
                                                     title=""
                                                     data-bs-original-title="Help">
                                                    Sidebar
                                                </div>
                                                <label class="switch">
                                                    <input type="checkbox"
                                                           id="sidebarToggler"
                                                           checked=""/>
                                                    <span class="slider round"/>
                                                </label>
                                            </div>
                                            <div class="sub_style">
                                                <div class=" t_settings info-infinito"
                                                     data-bs-toggle="popover"
                                                     data-bs-placement="right"
                                                     data-bs-content="Show App icon in sidebar"
                                                     title=""
                                                     data-bs-original-title="Help">
                                                    Show Icon
                                                </div>
                                                <label class="switch">
                                                    <input type="checkbox"
                                                           id="sidebarIconToggler"
                                                           checked=""/>
                                                    <span class="slider round"/>
                                                </label>
                                            </div>
                                            <div class="sub_style">
                                                <div class=" t_settings info-infinito"
                                                     data-bs-toggle="popover"
                                                     data-bs-placement="right"
                                                     data-bs-content="Show App name in sidebar"
                                                     title=""
                                                     data-bs-original-title="Help">
                                                    Show Name
                                                </div>
                                                <label class="switch">
                                                    <input type="checkbox"
                                                           id="sidebarNameToggler"
                                                           checked=""/>
                                                    <span class="slider round"/>
                                                </label>
                                            </div>
                                            <div class="sub_style">
                                                <div class=" t_settings info-infinito"
                                                     data-bs-toggle="popover"
                                                     data-bs-placement="right"
                                                     data-bs-content="Show company logo in top of app sidebar"
                                                     title=""
                                                     data-bs-original-title="Help">
                                                    Company Logo
                                                </div>
                                                <label class="switch">
                                                    <input type="checkbox"
                                                           id="sidebarCompanyToggler"
                                                           checked=""/>
                                                    <span class="slider round"/>
                                                </label>
                                            </div>
                                            <div class="sub_style">
                                                <div class="t_settings info-infinito"
                                                     data-bs-toggle="popover"
                                                     data-bs-placement="right"
                                                     data-bs-content="Show User Menu in top of app sidebar"
                                                     title=""
                                                     data-bs-original-title="Help">
                                                    User Menu
                                                </div>
                                                <label class="switch">
                                                    <input type="checkbox"
                                                           id="sidebarUserToggler"
                                                           checked=""/>
                                                    <span class="slider round"/>
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="button_properties">
                            <p>
                                <a class="btn btn-primary_style"
                                   data-bs-toggle="collapse" href="#navbar"
                                   role="button"
                                   aria-expanded="false" aria-controls="navbar">
                                    Navbar
                                </a>
                            </p>
                            <div class="collapse" id="navbar">
                                <div class="card card-body">
                                    <div class="sidebar_left">
                                        <div class="wrapper">
                                            <div class="sub_style">
                                                <div class="t_settings info-infinito"
                                                     data-bs-toggle="popover"
                                                     data-bs-placement="right"
                                                     data-bs-content="Only show navbar while hover top section of browser"
                                                     title=""
                                                     data-bs-original-title="Help">
                                                    Navbar on Hover
                                                </div>
                                                <label class="switch">
                                                    <input type="checkbox"
                                                           id="navbarHoverToggler"
                                                           checked=""/>
                                                    <span class="slider round"/>
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="button_properties">
                            <p>
                                <a class="btn btn-primary_style"
                                   data-bs-toggle="collapse" href="#dark"
                                   role="button"
                                   aria-expanded="false" aria-controls="dark">
                                    Dark mode
                                </a>
                            </p>
                            <div class="collapse" id="dark">
                                <div class="card card-body">
                                    <div class="sidebar_left">
                                        <div class="wrapper">
                                            <div class="sub_style">
                                                <div class=" t_settings info-infinito"
                                                     data-bs-toggle="popover"
                                                     data-bs-placement="right"
                                                     data-bs-content="Turn On Dark mode"
                                                     title=""
                                                     data-bs-original-title="Help">
                                                    Dark Mode
                                                </div>
                                                <label class="switch">
                                                    <input type="checkbox"
                                                           id="navbarDarkToggler"
                                                           checked=""
                                                           t-on-change="_OnChangeDark"/>
                                                    <span class="slider round"/>
                                                </label>
                                            </div>
                                            <div class="dark_mode">
                                                <ul class="mode dark-switch" t-on-click="onChangeDarkMode">
                                                    <li>
                                                        <a data-mode="all">
                                                            <i class="bi bi-brightness-high-fill"/>
                                                            <span>
                                                                All time
                                                            </span>
                                                        </a>
                                                    </li>
                                                    <li>
                                                        <a data-mode="schedule">
                                                            <i class="bi bi-clock"/>
                                                            <span>
                                                                Schedule
                                                            </span>
                                                        </a>
                                                    </li>
                                                    <li>
                                                        <a data-mode="auto">
                                                            <i class="bi bi-arrow-repeat"/>
                                                            <span>
                                                                Automatic
                                                            </span>
                                                        </a>
                                                    </li>
                                                </ul>
                                                <div class="on_off dark-schedule">
                                                    <ul>
                                                        <li class="d-flex">
                                                            <div class="left">Turn
                                                                On&#160;
                                                            </div>
                                                            <div class="right d-flex">
                                                                <span id="startSchedule"/>
                                                                <i class="fa fa-caret-right schedule-input"
                                                                   t-on-click="onClickSchedule"/>
                                                                <input type="text"
                                                                       style="display: none"
                                                                       id="time1"/>
                                                            </div>
                                                        </li>
                                                        <li class="d-flex">
                                                            <div class="left">Turn
                                                                Off&#160;
                                                            </div>
                                                            <div class="right d-flex">
                                                                <span id="endSchedule"/>
                                                                <i class="fa fa-caret-right schedule-input"
                                                                   t-on-click="onClickSchedule"/>
                                                                <input type="text"
                                                                       style="display: none"
                                                                       id="time2"/>
                                                            </div>
                                                        </li>
                                                    </ul>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="button_properties">
                            <p>
                                <a class="btn btn-primary_style"
                                   data-bs-toggle="collapse" href="#other"
                                   role="button"
                                   aria-expanded="false" aria-controls="other">
                                    Other
                                </a>
                            </p>
                            <div class="collapse" id="other">
                                <div class="card card-body">
                                    <div class="sidebar_left">
                                        <div class="wrapper">
                                            <div class="sub_style">
                                                <div class="t_settings info-infinito"
                                                     data-bs-toggle="popover"
                                                     data-bs-placement="right"
                                                     data-bs-content="Shows recent used apps on bottom of browser while hovering"
                                                     title=""
                                                     data-bs-original-title="Help">
                                                    Recent Apps
                                                </div>
                                                <label class="switch">
                                                    <input type="checkbox"
                                                           id="navbarRecentToggler"
                                                           checked=""/>
                                                    <span class="slider round"/>
                                                </label>
                                            </div>
                                            <div class="sub_style">
                                                <div class=" t_settings info-infinito"
                                                     data-bs-toggle="popover"
                                                     data-bs-placement="right"
                                                     data-bs-content="Enable Enterprise Like App menu"
                                                     title=""
                                                     data-bs-original-title="Help">
                                                    Full Screen App menu
                                                </div>
                                                <label class="switch">
                                                    <input type="checkbox"
                                                           id="navbarFullScreenAppToggler"
                                                           checked=""/>
                                                    <span class="slider round"/>
                                                </label>
                                            </div>
                                            <div class="sub_style">
                                                <div class="t_settings info-infinito"
                                                     data-bs-toggle="popover"
                                                     data-bs-placement="right"
                                                     data-bs-content="Can save menu as favorite and use it from Right side of  browser while hovering"
                                                     title=""
                                                     data-bs-original-title="Help">
                                                    Menu Bookmark
                                                </div>
                                                <label class="switch">
                                                    <input type="checkbox"
                                                           id="navbarMenuBookmarkToggler"
                                                           checked=""/>
                                                    <span class="slider round"/>
                                                </label>
                                            </div>
                                            <div class="sub_style">
                                                <div class=" t_settings info-infinito"
                                                     data-bs-toggle="popover"
                                                     data-bs-placement="right"
                                                     data-bs-content="Enable RTL"
                                                     title=""
                                                     data-bs-original-title="Help">
                                                    RTL
                                                </div>
                                                <label class="switch">
                                                    <input type="checkbox"
                                                           id="navbarRTLToggler"
                                                           checked=""/>
                                                    <span class="slider round"/>
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            <div class="sidebar_footer">
                     <a href="#" class="btn btn-submit close_changes"
                       t-on-click="_Close_changes">close
                    </a>

                    <a href="#" class="btn btn-submit js_save_changes"
                       t-on-click="_SaveChanges">Save Change
                    </a>
                </div>
            </div>
        </t>`;

    /**
     * Setup function to initialize the state and perform actions on component mount.
     */
    setup() {
        // Initialize component state using useState hook
        this.state = useState({
            // Define loaders array with default loader options
            loaders: ['default', 'ring', 'rotating', 'blinking', 'bounce'],
            loader: "",
            type: ['user', 'global'],
            fontData: null,
        })
        this.mode = session.infinitoDarkMode || 'all';
        this.darkStart = session.infinitoDarkStart || '19:00';
        this.darkEnd = session.infinitoDarkEnd || '5:00';
        this.darkStartFloat = this.timeToFloat(this.darkStart);
        this.darkEndFloat = this.timeToFloat(this.darkEnd);
        this.timePicker = new TimePicker(this);

        // Execute code when the component is mounted
        onMounted(async () => {
            // Set various toggler elements based on session values
            const userEditToggler = document.querySelector('#userEditToggler');
            if (userEditToggler) userEditToggler.checked = session.userEdit;

            const sidebarToggler = document.querySelector('#sidebarToggler');
            if (sidebarToggler) sidebarToggler.checked = session.sidebar;

            const sidebarIconToggler = document.querySelector('#sidebarIconToggler');
            if (sidebarIconToggler) sidebarIconToggler.checked = session.sidebarIco || session.sidebarIcon;

            const sidebarNameToggler = document.querySelector('#sidebarNameToggler');
            if (sidebarNameToggler) sidebarNameToggler.checked = session.sidebarName;

            const navbarHoverToggler = document.querySelector('#navbarHoverToggler');
            if (navbarHoverToggler) navbarHoverToggler.checked = session.fullscreen;

            const sidebarCompanyToggler = document.querySelector('#sidebarCompanyToggler');
            if (sidebarCompanyToggler) sidebarCompanyToggler.checked = session.sidebarCompany;

            const sidebarUserToggler = document.querySelector('#sidebarUserToggler');
            if (sidebarUserToggler) sidebarUserToggler.checked = session.sidebarUser;

            const navbarRecentToggler = document.querySelector('#navbarRecentToggler');
            if (navbarRecentToggler) navbarRecentToggler.checked = session.recentApps;

            const navbarFullScreenAppToggler = document.querySelector('#navbarFullScreenAppToggler');
            if (navbarFullScreenAppToggler) navbarFullScreenAppToggler.checked = session.fullScreenApp;

            // Sidebar and Full Screen App Menu are mutually exclusive layouts,
            // and exactly one of them should always be active — otherwise the
            // navbar falls back to the plain, unstyled default Odoo apps
            // dropdown. Reflect this live, radio-button style, as the user
            // toggles either one, instead of only enforcing it silently at
            // save time.
            if (sidebarToggler && navbarFullScreenAppToggler) {
                sidebarToggler.addEventListener('change', () => {
                    navbarFullScreenAppToggler.checked = !sidebarToggler.checked;
                });
                navbarFullScreenAppToggler.addEventListener('change', () => {
                    sidebarToggler.checked = !navbarFullScreenAppToggler.checked;
                });
            }

            const navbarDarkToggler = document.querySelector('#navbarDarkToggler');
            if (navbarDarkToggler) navbarDarkToggler.checked = session.infinitoDark;

            const navbarMenuBookmarkToggler = document.querySelector('#navbarMenuBookmarkToggler');
            if (navbarMenuBookmarkToggler) navbarMenuBookmarkToggler.checked = session.infinitoBookmark;

            const navbarRTLToggler = document.querySelector('#navbarRTLToggler');
            if (navbarRTLToggler) navbarRTLToggler.checked = session.infinitoRtl;

            // Initialize dark mode UI
            this.showDarkOptions(session.infinitoDark);

            // Set loader value
            const loaderSelect = document.querySelector('#loader');
            if (loaderSelect) loaderSelect.value = session.loaderClass || 'default';

            // Initialize popovers (assuming Bootstrap JS is loaded; data attributes handle hover)
            // No JS needed for popovers if using Bootstrap 5 data-bs- attributes
        });
    }

    async renderData() {

    }

    /**
     * Method to close the component and reload the page.
     * This method triggers a click event on the element with the ID 'hamburger' and reloads the page.
     */
    _Close() {
        // Trigger a click event on the element with ID 'hamburger' to close it
        const hamburger = document.querySelector('#hamburger');
        if (hamburger) {
            hamburger.click();
        }
        location.reload();
    }

    /**
     * Asynchronously saves the changes made by the user.
     * This method collects values from various toggler elements, updates session variables,
     * and sends the data to the server for further processing. Upon successful completion,
     * it triggers the `_Close` method to close the component.
     */
    async _SaveChanges() {
        const userEditToggler = document.querySelector('#userEditToggler');
        const isUserEdit = userEditToggler ? userEditToggler.checked : false;

        const vals = {
            userEdit: isUserEdit,
            sidebar: document.querySelector('#sidebarToggler')?.checked ?? false,
            sidebarIcon: document.querySelector('#sidebarIconToggler')?.checked ?? false,
            sidebarName: document.querySelector('#sidebarNameToggler')?.checked ?? false,
            fullscreen: document.querySelector('#navbarHoverToggler')?.checked ?? false,
            sidebarCompany: document.querySelector('#sidebarCompanyToggler')?.checked ?? false,
            sidebarUser: document.querySelector('#sidebarUserToggler')?.checked ?? false,
            recentApps: document.querySelector('#navbarRecentToggler')?.checked ?? false,
            fullScreenApp: document.querySelector('#navbarFullScreenAppToggler')?.checked ?? false,
            infinitoRtl: document.querySelector('#navbarRTLToggler')?.checked ?? false,
            infinitoDark: document.querySelector('#navbarDarkToggler')?.checked ?? false,
            infinitoBookmark: document.querySelector('#navbarMenuBookmarkToggler')?.checked ?? false,
            infinitoDarkMode: this.mode,
            infinitoDarkStart: this.darkStartFloat,
            infinitoDarkEnd: this.darkEndFloat,
            loaderClass: document.querySelector('#loader')?.value || 'default',
        };

        // Enforce logic
        if (vals.fullScreenApp && vals.sidebar) {
            vals.sidebar = false;
            document.querySelector('#sidebarToggler').checked = false;
        }
        // Enabling Full Screen App Menu above force-disables Sidebar. If the
        // user later turns Full Screen App Menu back off without touching
        // Sidebar themselves, restore it — otherwise both end up disabled and
        // the navbar silently falls back to the plain, unstyled default Odoo
        // apps dropdown instead of either custom layout.
        if (session.fullScreenApp && !vals.fullScreenApp && !vals.sidebar) {
            vals.sidebar = true;
            if (document.querySelector('#sidebarToggler')) {
                document.querySelector('#sidebarToggler').checked = true;
            }
        }
        if (!vals.sidebarIcon && !vals.sidebarName && vals.sidebar) {
            vals.sidebar = false;
            document.querySelector('#sidebarToggler').checked = false;
        }

        try {
            let result;
            if (isUserEdit) {
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

                //                    alert('Settings saved!');
                window.location.reload();
            }
        } catch (error) {
            console.error('SAVE FAILED:', error);
            alert('Failed to save: ' + (error.message || 'Unknown error'));
        }
    }

    /**
     * Reloads the window to discard changes and close the component.
     */
    _Close_changes() {
        window.location.reload();
    }

    /**
     * Handles the change event when the loader selection is modified.
     * @param {Event} ev - The event object representing the change event.
     */
    onLoaderChange(ev) {
        let val = ev.target.value;
        let loader = val == 'default' ? `<img src="/web/static/img/spin.svg" alt="Loading..."/>` : `<a href ="#" class="${val}"></a>`;
        let content = document.createElement('div');
        content.className = 'o_blockUI fixed-top d-flex justify-content-center align-items-center flex-column vh-100';
        content.innerHTML = `
                <div class="o_spinner mb-4">
                    ${loader}
                </div>
                <div class="o_message text-center px-4">
                    Loading...
                </div>`;
        const webClient = document.querySelector('.o_web_client');
        if (webClient) {
            webClient.appendChild(content);
        }
        setTimeout(() => {
            const blockUI = webClient.querySelector('.o_blockUI');
            if (blockUI) {
                blockUI.remove();
            }
        }, 3000)
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
        // Toggle display of dark switch based on the toggle status
        const darkSwitch = document.querySelector('.dark-switch');
        if (darkSwitch) {
            darkSwitch.style.display = toggle ? 'flex' : 'none';
        }
        // Toggle display of dark schedule based on the toggle status and mode
        const darkSchedule = document.querySelector('.dark-schedule');
        if (darkSchedule) {
            darkSchedule.style.display = (this.mode == 'schedule' && toggle) ? 'flex' : 'none';
        }
        // Highlight the active mode in the mode list
        let lis = document.querySelectorAll('.mode li');
        for (let li of lis) {
            const a = li.querySelector('a');
            if (a && a.dataset.mode == this.mode) {
                li.classList.add('active');
            } else {
                li.classList.remove('active');
            }
        }
    }

    /**
     * Handles the change event when the dark mode setting is modified.
     * @param {Event} ev - The event object representing the change event.
     */
    onChangeDarkMode(ev) {
        const target = ev.target.closest('a');
        if (target) {
            this.mode = target.dataset.mode;
            // Update UI for new mode
            this.showDarkOptions(document.querySelector('#navbarDarkToggler').checked);
            if (this.mode === 'auto') {
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
        // Assuming TimePicker handles the input show/hide
        const inputId = ev.target.nextElementSibling ? ev.target.nextElementSibling.id : null;
        if (inputId === 'time1') {
            this.timePicker.show(inputId, this.onChangeTime.bind(this));
        } else if (inputId === 'time2') {
            this.timePicker.show(inputId, this.onChangeTime2.bind(this));
        }
    }
}

export class EditorMenu extends Component {
    static template = xml` <t t-name="backend_theme_infinito.sidebar_simple_editor">
        <div class="sidebar_simple_editor">
            <Counter/>
        </div>
    </t>`;
    static components = {Counter};
}