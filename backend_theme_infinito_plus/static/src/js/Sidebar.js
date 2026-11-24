/** @odoo-module **/
import {Counter} from "@backend_theme_infinito/js/editor_menu";
import {onPatched, useRef, xml} from "@odoo/owl";
import {rpc} from "@web/core/network/rpc";
import {session} from "@web/session";
import {applyAnimation} from "./animation";

export class Sidebar extends Counter {
    static template = xml`<t>
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
                                            <div class="t_settings info-infinito"
                                                 data-bs-toggle="popover"
                                                 data-placement="right"
                                                 data-content="All internal users can edit their Advanced features for themselves"
                                                 title=""
                                                 data-original-title="Help">
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
                                                data-placement="right"
                                                data-content="All internal users can edit their Advanced features for themselves"
                                                title=""
                                                data-original-title="Help">
                                                Loaders
                                            </h6>
                                            <div class="sub_style">
                                                <select class="form-select infinito-form-select" id="loader" t-model="state.loader" t-on-change="onLoaderChange">
                                                    <option t-foreach="state.loaders" t-as="load" t-key="load" t-att-value="load" t-out="load"/>
                                                </select>
                                            </div>
                                        </div>
                                        <div class="sub_style">
                                            <div class="t_settings info-infinito"
                                                 data-bs-toggle="popover"
                                                 data-placement="right"
                                                 data-content="The theme colors will change to random colors every 10 minutes. Edited colors will remain unchanged."
                                                 title=""
                                                 data-original-title="Help">
                                                Chameleon Mode
                                            </div>
                                            <label class="switch">
                                                <input type="checkbox"
                                                       id="chameleonToggler"
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
                                                 data-placement="right"
                                                 data-content="Enables sidebar apps menu"
                                                 title=""
                                                 data-original-title="Help">
                                                Sidebar
                                            </div>
                                            <label class="switch">
                                                <input type="checkbox"
                                                       id="sidebarToggler"
                                                       checked="1"/>
                                                <span class="slider round"/>
                                            </label>
                                        </div>
                                        <div class="sub_style">
                                            <div class=" t_settings info-infinito"
                                                 data-bs-toggle="popover"
                                                 data-placement="right"
                                                 data-content="Show App icon in sidebar"
                                                 title=""
                                                 data-original-title="Help">
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
                                                 data-placement="right"
                                                 data-content="Show App name in sidebar"
                                                 title=""
                                                 data-original-title="Help">
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
                                                 data-placement="right"
                                                 data-content="Show company logo in top of app sidebar"
                                                 title=""
                                                 data-original-title="Help">
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
                                                 data-placement="right"
                                                 data-content="Show User Menu in top of app sidebar"
                                                 title=""
                                                 data-original-title="Help">
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
                                                 data-original-title="Help">
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
                                                 data-placement="right"
                                                 data-content="Turn On Dark mode"
                                                 title=""
                                                 data-original-title="Help">
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
                                                              t-on-click ="onClickSchedule"/>
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
                                                 data-placement="right"
                                                 data-content="Shows recent used apps on bottom of browser while hovering"
                                                 title=""
                                                 data-original-title="Help">
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
                                                 data-placement="right"
                                                 data-content="Enable Enterprise Like App menu"
                                                 title=""
                                                 data-original-title="Help">
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
                                                 data-placement="right"
                                                 data-content="Can save menu as favorite and use it from Right side of browser while hovering"
                                                 title=""
                                                 data-original-title="Help">
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
                                                 data-placement="right"
                                                 data-content="Enable RTL"
                                                 title=""
                                                 data-original-title="Help">
                                                RTL
                                            </div>
                                            <label class="switch">
                                                <input type="checkbox"
                                                       id="navbarRTLToggler"
                                                       checked=""/>
                                                <span class="slider round"/>
                                            </label>
                                        </div>
                                        <div class="sub_style">
                                            <div class=" t_settings info-infinito"
                                                 data-bs-toggle="popover"
                                                 data-placement="right"
                                                 data-content="Refresh the tree, kanban view"
                                                 title=""
                                                 data-original-title="Help">
                                                Refresh
                                            </div>
                                            <label class="switch">
                                                <input type="checkbox"
                                                       id="navbarRefreshToggler"
                                                       checked="" t-ref="navbarRefreshToggler"/>
                                                <span class="slider round"/>
                                            </label>
                                        </div>
                                        <div>
                                            <h6 class="info-infinito" data-bs-toggle="popover"
                                                data-placement="right"
                                                data-content="All internal users can edit their Advanced features for themselves"
                                                title="" data-original-title="Help">Fonts
                                            </h6>
                                            <div class="sub_style" id="js_fonts">
                                                <select id="infinito_font_select"
                                                        class="form-select infinito-form-select"
                                                        t-on-change="onFontChange"
                                                        t-on-click="_onAddGoogleFontClick">
                                                    <option class="form-select infinito-form-select system-font">System Font</option>
                                                    <option t-foreach="state.fontData or []" t-as="font" t-key="font.id" class="form-select infinito-form-select" t-att-data-id="font.id" t-att-value="font.id" t-out="font.name"/>
                                                    <option class="form-select infinito-form-select add-font">Add a Google Font</option>
                                                </select>
                                            </div>
                                        </div>
                                        <div>
                                            <h6 class="info-infinito" data-bs-toggle="popover"
                                                data-placement="right"
                                                data-content="All internal users can edit their Advanced features for themselves"
                                                title="" data-original-title="Help">Chatbox Position
                                            </h6>
                                            <div class="sub_style">
                                                <select class="form-select infinito-form-select" id="chatterbox_position">
                                                    <option t-foreach="chatBoxPosition" t-as="chatbox" t-key="chatbox" t-att-value="chatbox" t-att-selected="chatbox == session.chatBoxPosition" t-out="chatbox"/>
                                                </select>
                                            </div>
                                        </div>
                                        <div>
                                            <h6 class="info-infinito" data-bs-toggle="popover"
                                                data-placement="right"
                                                data-content="All internal users can edit their Advanced features for themselves"
                                                title="" data-original-title="Help">Animation
                                            </h6>
                                            <div class="sub_style">
                                                <select class="form-select infinito-form-select" id="animated_view" t-on-change="onAnimationChange">
                                                    <option t-foreach="infinitoAnimation" t-as="animation" t-key="animation" t-att-value="animation" t-att-selected="animation == (session.infinitoAnimation or 'Default')" t-out="animation"/>
                                                </select>
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
                       t-on-click="_Close_changes">Close</a>
                    <a href="#" class="btn btn-submit js_save_changes"
                       t-on-click="_SaveChanges">Save Changes</a>
                </div>
            </div>
        </div>
    </t>`;

    /**
     * Initializes the component variables and loads the font list.
     */
    setup() {
        super.setup();
        this.session = session;
        this.navbarRefreshToggler = useRef("navbarRefreshToggler");
        this.chatBoxPosition = ["Top Right", "Top Left", "Bottom Right", "Bottom Left"];
        this.infinitoAnimation = ["Default", "Scale", "Slide in"];
        this.font_id = parseInt(session.infinitoGoogleFont) || 0;
        this.renderData();

        // Patching session data after rendering
        onPatched(() => {
            const setChecked = (sel, val) => {
                const el = document.querySelector(sel);
                if (el) {
                    el.checked = !!val;
                }
            };
            const setValue = (sel, val) => {
                const el = document.querySelector(sel);
                if (el) {
                    el.value = val;
                }
            };
            setChecked("#userEditToggler", session.userEdit);
            setChecked("#sidebarToggler", session.sidebar);
            setChecked("#sidebarIconToggler", session.sidebarIcon);
            setChecked("#sidebarNameToggler", session.sidebarName);
            setChecked("#navbarHoverToggler", session.fullscreen);
            setChecked("#sidebarCompanyToggler", session.sidebarCompany);
            setChecked("#sidebarUserToggler", session.sidebarUser);
            setChecked("#navbarRecentToggler", session.recentApps);
            setChecked("#navbarFullScreenAppToggler", session.fullScreenApp);
            setChecked("#navbarDarkToggler", session.infinitoDark);
            setChecked("#navbarMenuBookmarkToggler", session.infinitoBookmark);
            setChecked("#chameleonToggler", session.infinitoChameleon);
            setChecked("#navbarRTLToggler", session.infinitoRtl);
            setChecked("#navbarRefreshToggler", session.infinitoRefresh);
            setValue("#chatterbox_position", session.chatBoxPosition);
            setValue("#animated_view", session.infinitoAnimation || "Default");
            setValue("#infinito_font_select", session.infinitoGoogleFont);
        });
    }

    /**
     * Loads the list of Google fonts (only their names).
     */
    async renderData() {
        super.renderData(...arguments);
        this.state.fontData = await rpc("/web/dataset/call_kw", {
            model: "infinito.google.font",
            method: "search_read",
            args: [],
            kwargs: {fields: ["name"]},
        });
    }

    /**
     * Previews the selected animation.
     * @param {Event} ev
     */
    onAnimationChange(ev) {
        applyAnimation(ev.target.value);
    }

    /**
     * Applies a font family to the whole UI with an injected <style> tag.
     * @param {string|null} fontName - Font family to apply, or null to reset.
     */
    _applyFont(fontName) {
        const old = document.getElementById("infinito-font-style");
        if (old) {
            old.remove();
        }
        const styleEl = document.createElement("style");
        styleEl.id = "infinito-font-style";
        if (!fontName) {
            styleEl.textContent = `
                * { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                    Roboto, "Helvetica Neue", Arial, sans-serif !important; }
                .fa { font: normal normal normal 14px/1 FontAwesome !important; }
                .oi { font-family: 'odoo_ui_icons' !important; }
            `;
        } else {
            styleEl.textContent = `
                * { font-family: '${fontName}', sans-serif !important; }
                .fa { font: normal normal normal 14px/1 FontAwesome !important; }
                .oi { font-family: 'odoo_ui_icons' !important; }
            `;
        }
        document.head.appendChild(styleEl);
    }

    /**
     * Applies the selected font immediately and stores its id for saving.
     * @param {Event} ev
     */
    onFontChange(ev) {
        const options = ev.target.options;
        const selected = options[options.selectedIndex];
        if (selected.classList.contains("add-font")) {
            return;
        }
        if (selected.classList.contains("system-font")) {
            this.font_id = 0;
            this._applyFont(null);
        } else {
            this.font_id = parseInt(selected.dataset.id);
            this._applyFont(selected.text.trim());
        }
    }

    /**
     * Opens the modal used to add a Google Font.
     */
    OpenModal() {
        const modalContainer = document.querySelector(
            ".o_action_manager .backend_theme_studio_sidebar");
        if (!modalContainer) {
            return;
        }
        modalContainer.innerHTML = `
            <div id="googleFontModal" class="modal">
                <div class="modal-content googleModal">
                    <div>
                        <div class="mb-3 row" style="margin-top: 16px;margin-left: 10px;">
                            <h6 style="font-size: medium; font-weight: bold;">Add a Google Font</h6>
                        </div>
                        <br/>
                        <div class="mb-3 row">
                            <label class="col-form-label col-md-3" for="google_font_html_infinito" style="margin-left: 32px;font-size: small;">Google Font address</label>
                            <div class="col-md-9">
                                <textarea id="google_font_html_infinito"
                                          class="form-control o_input_google_font"
                                          placeholder="https://fonts.google.com/specimen/Roboto"
                                          style="height: 88px;margin-left: 209px;margin-top: -29px;"></textarea>
                                <span class="float-end text-muted" style="margin-left:30px;font-size: small;">
                                    Select one font on <a target="_blank"
                                    href="https://fonts.google.com" style="font-size: small;color: #66598f;">fonts.google.com</a> and
                                    copy-paste the address of the font page here.
                                </span>
                            </div>
                            <br/>
                            <div style="margin-top:10px;">
                                <button class="btn btn-primary" id="saveBtn" style="background-color: var(--button-bg) !important;margin-left: 13px;">Save &amp; Reload</button>
                                <button class="btn btn-secondary" id="discardBtn">Discard</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        const modal = document.getElementById("googleFontModal");
        modal.style.display = "block";
        document.getElementById("saveBtn").addEventListener(
            "click", () => this._onSaveGoogleFont());
        document.getElementById("discardBtn").addEventListener("click", () => {
            modal.style.display = "none";
            window.location.reload();
        });
    }

    /**
     * Extracts the font name from a Google Fonts URL.
     * @param {string} url
     * @returns {string|null}
     */
    _getFontNameFromUrl(url) {
        const match = url.match(/[?&]family=([^&:]+)/) || url.match(/specimen\/([^/?#]+)/);
        return match ? decodeURIComponent(match[1].replace(/\+/g, " ")) : null;
    }

    /**
     * Saves the Google Font entered in the modal and reloads the page.
     */
    async _onSaveGoogleFont() {
        const url = document.querySelector(".o_input_google_font").value.trim();
        if (!url) {
            return;
        }
        const fontName = this._getFontNameFromUrl(url);
        if (!fontName) {
            this.env.services.notification.add(
                "Could not detect a Google Font name from that URL.",
                {type: "danger"});
            return;
        }
        await rpc("/web/dataset/call_kw", {
            model: "infinito.google.font",
            method: "save_google_fonts",
            args: [[fontName, url]],
            kwargs: {},
        });
        window.location.reload();
    }

    /**
     * Opens the modal when "Add a Google Font" is clicked.
     * @param {Event} ev
     */
    _onAddGoogleFontClick(ev) {
        if (ev.target.value === "Add a Google Font") {
            this.OpenModal();
        }
    }

    /**
     * Saves the Infinito Plus options, then lets the base method save the
     * other options and reload the page. The base method reloads the page
     * when it finishes, so it must run last.
     */
    async _SaveChanges() {
        const vals = {
            infinitoRefresh: document.querySelector("#navbarRefreshToggler").checked,
            infinitoGoogleFont: this.font_id,
            chatBoxPosition: document.querySelector("#chatterbox_position").value,
            infinitoAnimation: document.querySelector("#animated_view").value,
        };
        await rpc("/theme_studio/set_advanced_data_plus", {args: [{vals}]});
        return super._SaveChanges(...arguments);
    }
}