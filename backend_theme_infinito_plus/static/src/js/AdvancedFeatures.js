odoo.define('backend_theme_infinito_plus.AdvancedFeatures', function(require) {
    "use strict";
    const {mount} = owl;
    var AdvancedFeatures = require('backend_theme_infinito.AdvancedFeatures');
    var ajax = require('web.ajax');
    var session = require('web.session');
    var Dialog = require('web.Dialog');
    var core = require('web.core');
    var _t = core._t;
    var qweb = core.qweb;
    var rpc = require('web.rpc');
    // includes newly added features
    AdvancedFeatures.include({
        events: _.extend ({}, AdvancedFeatures.prototype.events, {
            'click #infinito_font_select': '_onAddGoogleFontClick',
            'change #infinito_font_select': 'onFontChange',
            'change #chatbox_position': 'onPositionChange',
            'change #animated_view': 'onAnimationChange',
        }),
        init: function(parent, type) {
            this._super.apply(this, arguments);
            this.chatBoxPosition = ['Top Right', 'Top Left', 'Bottom Right', 'Bottom Left']
            this.infinitoAnimation = ['Default', 'Scale', 'Slide in']
        },
        // function works when changing animations
        onAnimationChange: function(ev) {
            let options = ev.target.value
            if (options == 'Scale') {
                this.animated_id = 1
            } else if (options == 'Slide in') {
                this.animated_id = -1
            } else {
                this.animated_id = 0
            }
        },
        // function works when changing fonts
        onFontChange: function(ev) {
            let options = ev.target.options
            let selected = this.$(options[options.selectedIndex])
            if (selected.hasClass('add-font')) {
                return
            } else if (selected.hasClass('system-font')) {
                this.font_id = 0
            } else {
                this.font_id = parseInt(selected.data('id'))
            }
        },
        //render all the features while opening theme studio
        async renderData() {
            this.font_id = false
            this.chat_style = []
            this._super.apply(this, arguments);
            this.$el.find('#navbarRefreshToggler').attr('checked', session.infinitoRefresh);
            rpc.query({
                model: "infinito.google.font",
                method: 'search_read',
                args: [],
            }).then((data) => {
                this.$el.find('.infinito_font_select').html(qweb.render('theme_editor_sidebar_advanced_fonts', {
                    data
                }))
            });
            let position_content = '';
            for (let position of this.chatBoxPosition) { //append different positions to the selection as option
                position_content += `<option value="${position}">${position}</option>`;
            }
            this.$el.find('#chatbox_position').html(position_content);
            this.$el.find('#chatbox_position').val(session.chatBoxPosition);
            let animation_content = '';
            for (let animation of this.infinitoAnimation) { //append different animations to the selection as option
                animation_content += `<option value="${animation}">${animation}</option>`;
            }
            this.$el.find('#animated_view').html(animation_content);
            this.$el.find('#animated_view').val(session.infinitoAnimation);
        },
        // save the changes
        async _SaveChanges() {
            this._super.apply(this, arguments);
            let vals = {
                'infinitoRefresh': this.$el.find('#navbarRefreshToggler')[0].checked,
                'infinitoGoogleFont': this.font_id,
                'chatBoxPosition': this.$el.find('#chatbox_position').val(),
                'animations': this.animated_id,
                'infinitoAnimation': this.$el.find("#animated_view").val()
            }
            var chat_style = this.chat_style
            session.infinitoRefresh = vals.infinitoRefresh;
            session.chatBoxPosition = vals.chatBoxPosition;
            session.infinitoAnimation = vals.infinitoAnimation;
            // save animation from the selection
            var style = [];
            if (vals.animations == 1) {
                style = [];
                style.push('infinito_kanban_scale');
            } else if (vals.animations == 0) {
                style = [];
                style.push('infinito_kanban_shake');
            } else if (vals.animations == -1) {
                style = [];
                style.push('infinito_kanban_slide_in');
            }
            if (style.length != 0) {
                await ajax.jsonRpc('/theme_studio/animation_styles', 'call', {
                    'style': JSON.stringify(style)
                });
            }
            if (chat_style.length != 0) {
                await ajax.jsonRpc('/theme_studio/save_styles_plus', 'call', {
                    'new_style': JSON.stringify(chat_style)
                });
            }
            if (this.type == 'global') {
                await ajax.jsonRpc('/theme_studio/set_advanced_data_plus', 'call', {
                    vals
                }).then((_) => {
                    this._Close();
                })
            } else {
                await ajax.jsonRpc('/theme_studio/set_advanced_data_user_plus', 'call', {
                    vals
                }).then((_) => {
                    this._Close();
                })
            }
        },
        // on changing chatbox position
        async onPositionChange(ev) {
            let val = ev.target.value;
            var new_style = [];
            if (val == 'Top Right') {
                new_style = [];
                new_style.push({
                    'top': '10px',
                    'left': 'auto'
                });
            }
            if (val == 'Top Left') {
                new_style = [];
                new_style.push({
                    'top': '10px',
                    'left': '10px',
                    'right': 'auto'
                });
            }
            if (val == 'Bottom Left') {
                new_style = [];
                new_style.push({
                    'left': '10px',
                    'bottom': '10px',
                    'top': 'auto',
                    'right': 'auto'
                });
            }
            if (val == 'Bottom Right') {
                new_style = [];
                new_style.push({
                    'right': '10px',
                    'bottom': '10px',
                    'top': 'auto',
                    'left': 'auto'
                });
            }
            this.chat_style = new_style
        },
        // function works when clicking google font
        _onAddGoogleFontClick: function(ev) {
            var val = ev.target.value
            if (val == "Add a Google Font") {
                const dialog = new Dialog(this, {
                    title: _t("Add a Google Font"),
                    $content: $(core.qweb.render('backend_theme_infinito_plus.dialog.addGoogleFont')),
                    // open a wizard for selecting google font
                    buttons: [{
                            text: _t("Save & Reload"),
                            classes: 'btn-primary',
                            click: async () => {
                                const inputEl = dialog.el.querySelector('.o_input_google_font');
                                let m = inputEl.value.match(/\bfamily=([\w+]+)/);
                                // validation of link
                                if (m) {
                                    const font = m[1].replace(/\+/g, ' ');
                                    var self = this;
                                    rpc.query({
                                        model: "infinito.google.font",
                                        method: 'save_google_fonts',
                                        args: [
                                            [font, m.input]
                                        ],
                                    }).then(function(data) {});
                                    window.location.reload();
                                }
                            },
                        },
                        {
                            text: _t("Discard"),
                            close: true,
                        },
                    ],
                });
                dialog.open();
            }
        }
    });
});
