/** @odoo-module **/
/**
 * Imports necessary modules and dependencies for the component.
 */
import { Counter } from "@backend_theme_infinito/js/editor_menu";
import { useState,useRef,onPatched } from "@odoo/owl";
import { jsonrpc } from "@web/core/network/rpc_service";
import { useService } from "@web/core/utils/hooks";
const { xml } =owl;
import { session } from "@web/session";
export class Sidebar extends Counter{
    static template=xml`<t t-name="backend_theme_infinito.theme_editor_sidebar_advanced">
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
                                                     data-placement="right"
                                                     data-content="All internal users can edit their Advanced features for themself"
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
                                                    data-content="All internal users can edit their Advanced features for themself"
                                                    title=""
                                                    data-original-title="Help">
                                                    Loaders
                                                </h6>
                                                <div class="sub_style">
                                                <select class="form-select infinito-form-select" id="loader" t-model="state.loader" t-on-change="onLoaderChange">
                                                <t t-foreach="this.state.loaders" t-as="load" t-key="load.id">
                                                    <option t-att-value="load.name"><t t-esc="load.name"/></option>
                                                </t>
                                                </select>
                                                </div>
                                            </div>
                                            <div class="sub_style">
                                                <div class="t_settings info-infinito"
                                                     data-bs-toggle="popover"
                                                     data-placement="right"
                                                     data-content="Theme Color will change into a random colors every 10 minutes. Edited colors won't be changing"
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
                                                                On&amp;nbsp;
                                                            </div>
                                                            <div class="right d-flex">
                                                                <span id="startSchedule"/>
                                                                <i class="fa fa-caret-right schedule-input"
                                                                   t-on-change="onClickSchedule"/>
                                                                <input type="text"
                                                                       style="display: none"
                                                                       id="time1"/>
                                                            </div>
                                                        </li>
                                                        <li class="d-flex">
                                                            <div class="left">Turn
                                                                Off&amp;nbsp;
                                                            </div>
                                                            <div class="right d-flex">
                                                                <span id="endSchedule"/>
                                                                <i class="fa fa-caret-right schedule-input"
                                                                   t-on-change="onClickSchedule"/>
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
                                                     data-content="Can save menu as favorite and use it from Right side of  browser while hovering"
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
                                                    data-content="All internal users can edit their Advanced features for themself"
                                                    title="" data-original-title="Help">Fonts
                                                </h6>
                                                <div class="sub_style" id="js_fonts">
                                                    <select id="infinito_font_select"
                                                            class="form-select infinito-form-select " t-on-change="onFontChange" t-on-click="_onAddGoogleFontClick">
                                                    <option href="#" class="form-select infinito-form-select system-font"
                                                            t-att-data-variable="variable">System Font
                                                    </option>
                                                    <t t-if="this.state.fontData">
                                                        <t t-foreach="this.state.fontData" t-as="font" t-key="font.id">
                                                            <option href="#"
                                                                    class="form-select infinito-form-select"
                                                                    t-att-data-id="font.id" t-att-value="font.id">
                                                                <t t-esc="font.name"/>
                                                            </option>
                                                        </t>
                                                    </t>
                                                    <option href="#"
                                                            class="form-select infinito-form-select add-font"
                                                            t-att-data-variable="variable">Add a Google Font
                                                    </option>
                                                    </select>
                                                </div>
                                            </div>
                                            <div>
                                                <h6 class="info-infinito" data-bs-toggle="popover"
                                                    data-placement="right"
                                                    data-content="All internal users can edit their Advanced features for themself"
                                                    title="" data-original-title="Help">Chatbox Position
                                                </h6>
                                                <div class="sub_style">
                                                    <select class="form-select infinito-form-select"
                                                            id="chatterbox_position" t-on-change="onPositionChange">
                                                            <t t-foreach="this.chatBoxPosition" t-as="chatbox" t-key="chatbox.id">
                                                                <option t-att-value="chatbox" t-att-selected="chatbox == session.chatBoxPosition"><t t-esc="chatbox"/></option>
                                                            </t>
                                                    </select>
                                                </div>
                                            </div>
                                            <div>
                                                <h6 class="info-infinito" data-bs-toggle="popover"
                                                    data-placement="right"
                                                    data-content="All internal users can edit their Advanced features for themself"
                                                    title="" data-original-title="Help">Animation
                                                </h6>
                                                <div class="sub_style">
                                                     <select class="form-select infinito-form-select"
                                                             id="animated_view" t-on-change="onAnimationChange">
                                                         <t t-foreach="this.infinitoAnimation" t-as="animation" t-key="animation.id">
                                                            <option t-att-value="animation"><t t-esc="animation"/></option>
                                                         </t>
                                                     </select>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            <div class="sidebar_footer">
                    <a href="#" class="btn btn-submit js_save_changes"
                       t-on-click="_SaveChanges">Save Change
                    </a>
                </div>
            </div>
        </t>`;
        /**
         * Setup method for the component.
         * Initializes component variables and renders data.
         */
        setup(){
            super.setup();
            this.session = session
            this.navbarRefreshToggler = useRef("navbarRefreshToggler");
            this.chatBoxPosition = ['Top Right', 'Top Left', 'Bottom Right', 'Bottom Left'],
            this.infinitoAnimation = ['Default', 'Scale', 'Slide in'];
            this.renderData();

            // Patching session data after rendering
            onPatched(async() => {
                document.querySelector('#userEditToggler').checked = session.userEdit;
                document.querySelector('#sidebarToggler').checked = session.sidebar;
                document.querySelector('#sidebarIconToggler').checked = session.sidebarIco;
                document.querySelector('#sidebarNameToggler').checked = session.sidebarName;
                document.querySelector('#navbarHoverToggler').checked = session.fullscreen;
                document.querySelector('#sidebarCompanyToggler').checked = session.sidebarCompany;
                document.querySelector('#sidebarUserToggler').checked = session.sidebarUser;
                document.querySelector('#navbarRecentToggler').checked = session.recentApps;
                document.querySelector('#navbarFullScreenAppToggler').checked = session.fullScreenApp;
                document.querySelector('#navbarDarkToggler').checked=session.infinitoDark;
                document.querySelector('#navbarMenuBookmarkToggler').checked = session.infinitoBookmark;
                document.querySelector('#chameleonToggler').checked=session.infinitoChameleon;
                document.querySelector('#navbarRTLToggler').checked=session.infinitoRtl;
                document.querySelector('#navbarRefreshToggler').checked=session.infinitoRefresh;
                document.querySelector('#chatterbox_position').value=session.chatBoxPosition;
                document.querySelector('#animated_view').value = session.infinitoAnimation || 'Default';
                document.querySelector("#infinito_font_select").value=session.infinitoGoogleFont;
            });
        }
        /**
         * Asynchronously renders data for the component.
         * Retrieves font data from the server.
         */
        async renderData(){
            var self=this;
            this.font_id = false
            this.chat_style = []
            this.data={}
            super.renderData(...arguments);
            await jsonrpc('/web/dataset/call_kw',{
                model:'infinito.google.font',
                method:'search_read',
                args: [],
                kwargs: {},
            }).then((data)=>{
                self.state.fontData=data;
            });
        }
        /**
         * Handles the animation change event.
         * Sets the animation ID based on the selected option.
         * @param {Event} ev - The event object.
         */
        async onAnimationChange(ev){
            let options = ev.target.value
             if (options == 'Scale') {
                this.animated_id = 1
             }else if (options == 'Slide in') {
                this.animated_id = -1
             }else {
                this.animated_id = 0
             }
        }
        /**
         * Handles the font change event.
         * Sets the font ID based on the selected option.
         * @param {Event} ev - The event object.
         */
        onFontChange(ev){
            let options = ev.target.options
            let selected = options[options.selectedIndex];
            if (selected.classList.contains('add-font')) {
                return
            }else if (selected.classList.contains('system-font')){
                this.font_id = 0
            }else {
                this.font_id = parseInt(selected.dataset.id)
            }
        }
        /**
         * Opens the modal for adding Google Font.
         * Inserts the modal content into the sidebar container.
         * @returns {void}
         */
        OpenModal(){
           var modalContainer = document.querySelector('.o_action_manager .backend_theme_studio_sidebar');
           var modalContent = `
                <div id="googleFontModal" class="modal">
                    <div class="modal-content googleModal">
                        <div t-name="backend_theme_infinito_plus.dialog.addGoogleFont">
                        <div class="mb-3 row" style="margin-top: 16px;margin-left: 10px;">
                            <h6 style="font-size: medium; font-weight: bold;">Add a Google Font</h6></div>
                            </br>
                            <div class="mb-3 row">
                                <label class="col-form-label col-md-3" for="google_font_html" style="margin-left: 32px;font-size: small;">Google Font address</label>
                                <div class="col-md-9">
                                    <textarea id="google_font_html_infinito"
                                            class="form-control o_input_google_font"
                                            placeholder="https://fonts.google.com/specimen/Roboto"
                                            style="height: 88px;margin-left: 209px;margin-top: -29px; "></textarea>
                                    <span class="float-end text-muted" style="margin-left:30px;font-size: small;"">
                                        Select one font on <a target="_blank"
                                                            href="https://fonts.google.com" style="font-size: small;color: #66598f;">fonts.google.com</a> and
                                        copy-paste the address of the font page here.
                                    </span>
                                </div>
                                <br/>
                                <div style="margin-top:10px;">
                                <button class="btn btn-primary" id="saveBtn" style=" background-color: var(--button-bg) !important;margin-left: 13px;">Save & Reload</button>
                                <button class="btn btn-secondary" id="discardBtn">DISCARD</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            modalContainer.innerHTML = modalContent;
            var modal = document.getElementById('googleFontModal');
            modal.style.display = 'block';
            var saveBtn = document.getElementById('saveBtn')
            saveBtn.addEventListener('click',function(){
                const inputEl = document.querySelector('.o_input_google_font');
                let m = inputEl.value.match(/\bfamily=([\w+]+)/);
                if (m) {
                    const font = m[1].replace(/\+/g, ' ');
                    jsonrpc('/web/dataset/call_kw',{
                        model:'infinito.google.font',
                        method:'save_google_fonts',
                        args: [[font, m.input]],
                        kwargs: {},
                    }).then((result)=>{});
                    window.location.reload();
                }
            });
            var discardBtn = document.getElementById('discardBtn');
             discardBtn.addEventListener('click', function() {
                modal.style.display = 'none';
                location.reload();
             });
        }
        /**
         * Handles the click event for adding a Google Font.
         * Opens the modal if the clicked value is "Add a Google Font".
         * @param {Event} ev - The event object.
         */
        _onAddGoogleFontClick(ev){
            var val = ev.target.value
            if (val == "Add a Google Font") {
                this.OpenModal();
            }
        }
        /**
         * Handles the position change event for the chat box.
         * Sets the new style based on the selected position.
         * @param {Event} ev - The event object.
         * @returns {void}
         */
        async onPositionChange(ev){
            let val = ev.target.value;
            var new_style = [];
            if (val === 'Top Right') {
                new_style = { top: '10px', left: 'auto' };
            } else if (val === 'Top Left') {
                new_style = { top: '10px', left: '10px', right: 'auto' };
            } else if (val === 'Bottom Left') {
                new_style = { left: '10px', bottom: '10px', top: 'auto', right: 'auto' };
            } else if (val === 'Bottom Right') {
                new_style = { right: '10px', bottom: '10px', top: 'auto', left: 'auto' };
            }
            this.chat_style = new_style
        }
        /**
         * Saves the changes made in the advanced settings.
         * Updates session data and triggers necessary actions.
         * @returns {void}
         */
        async _SaveChanges() {
            super._SaveChanges(...arguments);
             let vals = {
                'infinitoRefresh':document.querySelector('#navbarRefreshToggler').checked,
                'infinitoGoogleFont':this.font_id,
                'chatBoxPosition':document.querySelector('#chatterbox_position').value,
                'animations': this.animated_id,
                'infinitoAnimation':document.querySelector('#animated_view').value,
             }
              var chat_style = this.chat_style
              session.infinitoRefresh = vals.infinitoRefresh;
              session.chatBoxPosition = vals.chatBoxPosition;
              session.infinitoAnimation = vals.infinitoAnimation;
              session.infinitoGoogleFont =vals.infinitoGoogleFont;
              var style = [];
              if (vals.animations == 1) {
                    style = [];
                    style.push('infinito_kanban_scale');
              } else if (vals.animations == 0) {
                    style = [];
                    style.push('infinito_kanban_shake');
              }else if (vals.animations == -1) {
                    style = [];
                    style.push('infinito_kanban_slide_in');
              }
              if (style.length != 0) {
                  await jsonrpc('/theme_studio/animation_styles',{
                    method:'call',
                    kwargs:{
                        'style': JSON.stringify(style),
                    }
                  });
              }
              if (chat_style.length != 0) {
                await jsonrpc('/theme_studio/save_styles_plus', {
                    method: 'call',
                    kwargs:{
                        'new_style': JSON.stringify(chat_style)
                    }
                });
             }
             await jsonrpc('/theme_studio/set_advanced_data_plus', {
                        method:'call',
                        args: [{ vals }],
             }).then((_) => {
                 this._Close();
             })
        }
}
