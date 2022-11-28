odoo.define('backend_theme_infinito.AdvancedFeatures', function (require) {
    "use strict";
    const { mount} = owl;

    var Widget = require('backend_theme_infinito.ThemeStudioWidget');
    var TimePicker = require('backend_theme_infinito.timepicker');
    var ajax = require('web.ajax');
    var session = require('web.session');
    var AdvancedFeatures = Widget.extend({
        template: 'theme_editor_sidebar_advanced',
        events: {
            'click .close_advanced': '_Close',
            'click .js_save_changes': '_SaveChanges',
            'change #navbarDarkToggler': '_OnChangeDark',
            'click .mode li': 'onChangeDarkMode',
            'click .schedule-input': 'onClickSchedule',
            'change #loader': 'onLoaderChange'
        },
        current_tools: [],
        init: function (parent, type) {
            this._super.apply(this, arguments);
            this.parent = parent;
            this.sidebar_width = '330px';
            this.mode = session.infinitoDarkMode || 'all';
            this.darkStart = session.infinitoDarkStart || '19:00';
            this.darkEnd = session.infinitoDarkEnd || '5:00';
            this.darkStartFloat = this.timeToFloat(this.darkStart);
            this.darkEndFloat = this.timeToFloat(this.darkEnd);
            this.type = type;
            if(this.type == 'user'){
                this.appendTo(document.body)
            }
            this.loaders = ['default', 'ring', 'rotating', 'blinking', 'bounce']
        },

        start: function () {
            this._super.apply(this, arguments);
            this._Open();
            this.renderData();
            this.timePicker = new TimePicker(this);
            this.timePicker.appendTo($(document.body));
            this.$el.next().removeClass('marg_main');
            if (this.mode == 'schedule'){
                $('.dark-schedule').css('display', 'flex');
            } else {
                $('.dark-schedule').css('display', 'none');
            }
            this.$('.info-infinito').popover({
                trigger: 'hover'
            });
        },
        _Open: function(){
            this.$el.css('width', this.sidebar_width);
            if(this.type == 'global'){
                this.$el.parent().next().css('margin-left', this.sidebar_width)
                this.$el.css('height', '91.4vh');
            } else {
                this.$el.parent().css('margin-right', this.sidebar_width)
                this.$el.css('right', '0');
                this.$el.css('left', 'initial');
                this.$el.css('height', '100vh');
            }
        },
        _Close: function() {
            $('#hamburger').click()
            this.$el.css('width', '0');
            if(this.type == 'global'){
                this.$el.parent().next().css('margin-left', '0');
            } else {
                this.$el.parent().css('margin-right', '0');
                location.reload();
            }
        },
        async renderData(){
            this.$el.find('#userEditToggler').attr('checked', session.userEdit);
            this.$el.find('#sidebarToggler').attr('checked', session.sidebar);
            this.$el.find('#sidebarIconToggler').attr('checked', session.sidebarIcon);
            this.$el.find('#sidebarNameToggler').attr('checked', session.sidebarName);
            this.$el.find('#navbarHoverToggler').attr('checked', session.fullscreen);
            this.$el.find('#sidebarCompanyToggler').attr('checked', session.sidebarCompany);
            this.$el.find('#sidebarUserToggler').attr('checked', session.sidebarUser);
            this.$el.find('#navbarRecentToggler').attr('checked', session.recentApps);
            this.$el.find('#navbarFullScreenAppToggler').attr('checked', session.fullScreenApp);
            this.$el.find('#navbarRTLToggler').attr('checked', session.infinitoRtl);
            this.$el.find('#navbarDarkToggler').attr('checked', session.infinitoDark);
            this.$el.find('#navbarMenuBookmarkToggler').attr('checked', session.infinitoBookmark);
            this.$el.find('#chameleonToggler').attr('checked', session.infinitoChameleon);
            let content = '';
            for(let loader of this.loaders){
                content += `<option value="${loader}">${loader}</option>`;
            }
            this.$el.find('#loader').html(content);
            this.$el.find('#loader').val(session.loaderClass);
            this.showDarkOptions(session.infinitoDark);
            this.$el.find(`[data-mode="${this.mode}"]`).closest('li').addClass('active');
            this.setRender();
            this.hideOptions();
        },
        setRender: function(){
            this.$el.find('#startSchedule').html(this.darkStart);
            this.$el.find('#endSchedule').html(this.darkEnd);
            this.$el.find('#item1').val(session.infinitoDarkStart);
            this.$el.find('#item2').val(session.infinitoDarkEnd);
        },
        hideOptions: function(){
            if(this.type == 'user'){
                this.$el.find('#userEditToggler').closest('.sub_style').remove();
            }
        },
        async _SaveChanges(){
            let vals = {
                'sidebar': this.$el.find('#sidebarToggler')[0].checked,
                'sidebarIcon': this.$el.find('#sidebarIconToggler')[0].checked,
                'sidebarName': this.$el.find('#sidebarNameToggler')[0].checked,
                'fullscreen': this.$el.find('#navbarHoverToggler')[0].checked,
                'sidebarCompany': this.$el.find('#sidebarCompanyToggler')[0].checked,
                'sidebarUser': this.$el.find('#sidebarUserToggler')[0].checked,
                'recentApps': this.$el.find('#navbarRecentToggler')[0].checked,
                'fullScreenApp': this.$el.find('#navbarFullScreenAppToggler')[0].checked,
                'infinitoRtl': this.$el.find('#navbarRTLToggler')[0].checked,
                'infinitoDark': this.$el.find('#navbarDarkToggler')[0].checked,
                'infinitoBookmark': this.$el.find('#navbarMenuBookmarkToggler')[0].checked,
                'infinitoChameleon': this.$el.find('#chameleonToggler')[0].checked,
                'infinitoDarkMode': this.mode,
                'infinitoDarkStart': this.darkStartFloat,
                'infinitoDarkEnd': this.darkEndFloat,
                'loaderClass': this.$el.find('#loader').val(),
            }
            if(!vals.sidebarIcon && !vals.sidebarName && vals.sidebar){
                vals.sidebar = false;
                this.$(".error-message").html('Sidebar is <b>disabled</b> due to icon and name is disabled');
                this.$(".error-message").animate({
                    left: 0,
                },
                1000,
                function () {
                    $(this).delay(3000).fadeOut();
                });
            } if(vals.fullScreenApp && vals.sidebar) {
                vals.sidebar = false;
                this.$(".error-message").html('Sidebar is <b>disabled</b>, only sidebar or fullscreen app show at a time');
                this.$(".error-message").animate({
                    left: 0,
                },
                1000,
                function () {
                    $(this).delay(3000).fadeOut();
                });
            }
            session.sidebar = vals.sidebar;
            session.sidebarIcon = vals.sidebarIcon;
            session.sidebarName = vals.sidebarName;
            session.fullscreen = vals.fullscreen;
            session.sidebarCompany = vals.sidebarCompany;
            session.sidebarUser = vals.sidebarUser;
            session.recentApps = vals.recentApps;
            session.fullScreenApp = vals.fullScreenApp;
            session.infinitoBookmark = vals.infinitoBookmark;
            session.infinitoDark = vals.infinitoDark;
            session.infinitoDark = vals.infinitoDark;
            session.infinitoChameleon = vals.infinitoChameleon;
            session.infinitoDarkMode = this.mode;
            session.infinitoDarkStart = this.darkStart;
            session.infinitoDarkEnd = this.darkEnd;
            session.loaderClass = vals.loaderClass;
            if(this.type == 'global'){
                session.userEdit = this.$el.find('#userEditToggler')[0].checked;
                vals.userEdit = this.$el.find('#userEditToggler')[0].checked;
                await ajax.jsonRpc('/theme_studio/set_advanced_data', 'call', {vals}).then((_) => {
                    this._Close();
                })
            } else {
                await ajax.jsonRpc('/theme_studio/set_advanced_data_user', 'call', {vals}).then((_) => {
                    this._Close();
                })
            }
        },
        _OnChangeDark: function(ev){
            this.showDarkOptions(ev.target.checked);
        },
        showDarkOptions: function(toggle){
            if(toggle){
                $('.dark-switch').css('display', 'flex');
            } else {
                $('.dark-switch').css('display', 'none');
            }
            if (this.mode == 'schedule' && toggle){
                $('.dark-schedule').css('display', 'flex');
            } else {
                $('.dark-schedule').css('display', 'none');
            }
            let lis = this.$el.find('.mode li');
            for(let li of lis){
                if($(li).find('a').data('mode') == this.mode){
                    $(li).addClass('active');
                } else {
                    $(li).removeClass('active');
                }
            }
        },
        onChangeDarkMode: function(ev){
            if($(ev.target).nodeName == 'LI'){
                this.mode = $(ev.target).find('a').data('mode');
            } else {
                this.mode = $(ev.target).parent().data('mode');
            }
            this.showDarkOptions(true);
            if(this.mode == 'auto') {
                this.darkStartFloat = 19.0;
                this.darkEndFloat = 5.0;
            }
            if (this.mode == 'schedule'){
                $('.dark-schedule').css('display', 'flex');
            } else {
                $('.dark-schedule').css('display', 'none');
            }
        },
        onClickSchedule: function(ev){
            this.timePicker.$el.removeClass('d-none')
            this.timePicker.attach({
                target: this.$(ev.target).next()[0],
                "24" : true,
                time: this.$(ev.target).next()[0].id == 'time1' ? this.darkStart : this.darkEnd,
            });
        },
        onChangeTime: function(ev){
            this.darkStartFloat = this.timeToFloat(ev.target.value);
            this.darkStart = ev.target.value;
            this.setRender();
        },
        onChangeTime2: function(ev){
            this.darkEndFloat = this.timeToFloat(ev.target.value);
            this.darkEnd = ev.target.value;
            this.setRender();
        },
        floatToTime: function(number){
            let hour = Math.floor(number);
            let decpart = number - hour;
            let min = 1 / 60;
            decpart = min * Math.round(decpart / min);
            let minute = Math.floor(decpart * 60) + '';
            if (minute.length < 2) {
                minute = '0' + minute;
            }
            let time = hour + ':' + minute;
            return time;
        },
        timeToFloat: function(time){
            time = time.split(':');
            let decpart = 0
            if(time[1] && parseInt(time[1]) > 0){
                decpart = parseInt(time[1]) * 1.666;
            }
            let floatString = `${time[0]}.${Math.round(decpart)}`;
            return parseFloat(floatString)
        },
        onLoaderChange: function(ev){
            let val = ev.target.value;
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
            if(!session.userEdit || this.parent.$el) {
                this.parent.$el.find('.previews').html(content);
                setTimeout(()=>{
                    this.parent.$el.find('.previews').html('');
                }, 3000)
            } else {
                $('.o_web_client').append(content);
                setTimeout(()=>{
                    $('.o_web_client').find('.o_blockUI').remove();
                }, 3000)
            }

        },
        destroy: function(){
            this._super.apply(this, arguments);
        },
        render: function(){
            this._super.apply(this, arguments);
            mount(TimePicker, document.body);
        }

    });

    return AdvancedFeatures;

});