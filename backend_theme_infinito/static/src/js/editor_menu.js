/** @odoo-module **/
import { ThemeStudioWidget } from "./ThemeStudioWidget";
import { Component,  useState, mount, xml, onWillStart,useEnv,onMounted } from "@odoo/owl";
import { session } from "@web/session";
import { TimePicker } from "./timepicker";
import { jsonrpc } from "@web/core/network/rpc_service";
import { BlockUI } from "@web/core/ui/block_ui";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";

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
                                                           checked=""/>
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
        setup(){
            // Initialize component state using useState hook
           this.state=useState({
                // Define loaders array with default loader options
                loaders:[{'id':1, 'name':'default' },{'id':2,'name': 'ring'},{'id':3,'name':'rotating'},{'id':4,'name':'blinking'},{'id':5,'name':'bounce'}],
                loader:"",
                type:[{'id':1,'name':'user'},{'id':2,'name':'global'}],
                fontData:null,
            })
             // Execute code when the component is mounted
            onMounted(async() => {
                // Set various toggler elements based on session values
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
                document.querySelector('#navbarRTLToggler').checked=session.infinitoRtl;
            });
         }
         /**
         * Constructor function for initializing the component.
         * @param {Object} parent - The parent element of the component.
         * @param {string} type - Type of the component.
         */
        constructor(parent,type) {
            // Call the constructor of the parent class
            super(...arguments);
            this.parent = parent;
            this.sidebar_width = '330px';
            this.mode = session.infinitoDarkMode || 'all';
            this.darkStart = session.infinitoDarkStart || '19:00';
            this.darkEnd = session.infinitoDarkEnd || '5:00';
            this.timePicker = new TimePicker(this);
            if (this.mode == 'schedule'){
                $('.dark-schedule').css('display', 'flex');
            } else {
                $('.dark-schedule').css('display', 'none');
            }
            $('.info-infinito').popover({
                trigger: 'hover'
            });
            if (this.state.type == 'user') {
                this.appendTo(document.body);
            }
            this.state.loaders = ['default', 'ring', 'rotating', 'blinking', 'bounce'];
        }
        async renderData(){

        }
        /**
         * Method to close the component and reload the page.
         * This method triggers a click event on the element with the ID 'hamburger' and reloads the page.
         */
        _Close () {
            // Trigger a click event on the element with ID 'hamburger' to close it
            $('#hamburger').click()
             location.reload();
        }
        /**
         * Asynchronously saves the changes made by the user.
         * This method collects values from various toggler elements, updates session variables,
         * and sends the data to the server for further processing. Upon successful completion,
         * it triggers the `_Close` method to close the component.
         */
        async _SaveChanges(){
            // Collect values from various toggler elements
            let vals = {
                'userEditToggler':document.querySelector('#userEditToggler').checked,
                'sidebar': document.querySelector('#sidebarToggler').checked,
                'sidebarIcon': document.querySelector('#sidebarIconToggler').checked,
                'sidebarName': document.querySelector('#sidebarNameToggler').checked,
                'fullscreen': document.querySelector('#navbarHoverToggler').checked,
                'sidebarCompany': document.querySelector('#sidebarCompanyToggler').checked,
                'sidebarUser': document.querySelector('#sidebarUserToggler').checked,
                'recentApps': document.querySelector('#navbarRecentToggler').checked,
                'fullScreenApp': document.querySelector('#navbarFullScreenAppToggler').checked,
                'infinitoRtl': document.querySelector('#navbarRTLToggler').checked,
                'infinitoDark': document.querySelector('#navbarDarkToggler').checked,
                'infinitoBookmark': document.querySelector('#navbarMenuBookmarkToggler').checked,
                'infinitoDarkMode': this.mode,
                'infinitoDarkStart': this.darkStartFloat,
                'infinitoDarkEnd': this.darkEndFloat,
                'loaderClass': document.querySelector('#loader').value,
            }
            if(!vals.sidebarIcon && !vals.sidebarName && vals.sidebar){
                vals.sidebar = false;
            } if(vals.fullScreenApp && vals.sidebar){
                vals.sidebar = false;
            }
            session.userEdit = document.querySelector('#userEditToggler').checked;
            session.sidebar = vals.sidebar;
            session.sidebarIcon = vals.sidebarIcon;
            session.sidebarName = vals.sidebarName;
            session.fullscreen = vals.fullscreen;
            session.infinitoRtl=vals.infinitoRtl;
            session.sidebarCompany = vals.sidebarCompany;
            session.sidebarUser = vals.sidebarUser;
            session.recentApps = vals.recentApps;
            session.fullScreenApp = vals.fullScreenApp;
            session.infinitoBookmark = vals.infinitoBookmark;
            session.infinitoDark = vals.infinitoDark;
            session.infinitoDarkMode = this.mode;
            session.infinitoDarkStart = this.darkStart;
            session.infinitoDarkEnd = this.darkEnd;
            session.loaderClass = vals.loaderClass;
            await jsonrpc('/theme_studio/set_advanced_data', {
                method: 'call',
                args: [{ vals }],
            }).then((_) => {
                this._Close();
            });
        }
        /**
         * Reloads the window to discard changes and close the component.
         */
        _Close_changes(){
            // Reload the window to discard changes and close the component
            window.location.reload();
        }
        /**
         * Handles the change event when the loader selection is modified.
         * @param {Event} ev - The event object representing the change event.
         */
        onLoaderChange(ev){
            // Activate BlockUI (assuming BlockUI is a function that should be called here)
            BlockUI;
            let val=ev.target.value;
            console.log(val)
            let loader = val == 'default' ? `<img src="/web/static/img/spin.png" alt="Loading..."/>` : `<a href ="#" class="${val}"></a>` ;
            let content = `
                <div class="o_blockUI">
                    <div class="o_spinner">
                        ${loader}
                    </div>
                    <div class="o_message">
                        Loading...
                    </div>
                </div>`;
            console.log(document.querySelectorAll(".o_web_client"))
            $('.o_web_client').append(content);
            setTimeout(()=>{
                    $('.o_web_client').find('.o_blockUI').remove();
                }, 3000)
        }
        /**
         * Handles the change event when the time selection is modified.
         * @param {Event} ev - The event object representing the change event.
         */
         onChangeTime (ev){
             // Convert the selected time to a float value and assign it to darkStartFloat
            this.darkStartFloat = this.timeToFloat(ev.target.value);
            this.darkStart = ev.target.value;
        }
        /**
         * Handles the change event when the second time selection is modified.
         * @param {Event} ev - The event object representing the change event.
         */
        onChangeTime2 (ev){
            // Convert the selected time to a float value and assign it to darkEndFloat
            this.darkEndFloat = this.timeToFloat(ev.target.value);
            this.darkEnd = ev.target.value;
        }
        /**
         * Handles the change event when the dark mode option is modified.
         * @param {Event} ev - The event object representing the change event.
         */
         _OnChangeDark(ev){
            // Call the showDarkOptions method with the checked status of the target element
            this.showDarkOptions(ev.target.checked);
         }
         /**
         * Displays or hides dark mode options based on the toggle status.
         * @param {boolean} toggle - The toggle status indicating whether to show or hide the dark mode options.
         */
         showDarkOptions(toggle){
            // Toggle display of dark switch based on the toggle status
            if(toggle){
                $('.dark-switch').css('display', 'flex');
            }else{
                $('.dark-switch').css('display', 'none');
            }
            // Toggle display of dark schedule based on the toggle status and mode
            if (this.mode == 'schedule' && toggle){
                $('.dark-schedule').css('display', 'flex');
            }else{
                $('.dark-schedule').css('display', 'none');
            }
            // Highlight the active mode in the mode list
            let lis = document.querySelectorAll('.mode li');
            for(let li of lis){
                if($(li).find('a').data('mode') == this.mode){
                    $(li).addClass('active');
                } else {
                    $(li).removeClass('active');
                }
            }
         }
         /**
         * Handles the change event when the dark mode setting is modified.
         * @param {Event} ev - The event object representing the change event.
         */
         onChangeDarkMode (ev){
            // Check if the current mode is 'auto'
            if(this.mode == 'auto') {
                // Set default start and end times if in 'auto' mode
                this.darkStartFloat = 19.0;
                this.darkEndFloat = 5.0;
            }
         }
  state = useState({ value: 0 });
}
export class EditorMenu extends Component{
    static template = xml` <t t-name="backend_theme_infinito.sidebar_simple_editor">
        <div class="sidebar_simple_editor">
            <Counter/>
        </div>
    </t>`;
    static components = { Counter };
}
