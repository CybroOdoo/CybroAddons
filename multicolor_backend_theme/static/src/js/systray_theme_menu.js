/** @odoo-module **/
import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';
import Session from 'web.session';
import {patch} from 'web.utils';
import {Discuss} from "@mail/components/discuss/discuss";
var core = require('web.core');
var session = require('web.session');
var QWeb = core.qweb;
var rpc = require('web.rpc');
var ControlPanel = require('web.ControlPanel');
var DropdownMenu = require('web.DropdownMenu');
var FormRenderer = require('web.FormRenderer');
var ListRenderer = require('web.ListRenderer');
var KanbanRenderer = require('web.KanbanRenderer');
var KanbanRecord = require('web.KanbanRecord');
var AbstractController = require('web.AbstractController');
var utils = require('web.utils');
var selected_theme = {};
var themes_to_update = {};
var Temple = Widget.extend({
    name: 'activity_menu',
    template: 'multicolor_backend_theme.systray.ThemeMenu',
    events: {
        'click .themes_selector_button': '_onThemeSelectorClick',
        'change .theme_select': '_onThemeClick',
        'click .button-create': '_onThemeCreate',
        'click .button-remove': '_onThemeRemove',
        'click .button-apply': '_onThemeApply',
        'click .row.name i.fa-pencil': '_onNameEdit',
        'click .row.name i.fa-check': '_onNameSave',
        'change .row.name input#name': '_onNameSave',
        'keyup .row.name input#name': '_onNameChange',
        'click .color': '_colorPick'
    },
    start: function() {
        this._loadDefaults();
        this._apply_theme();
        return this._super();
    },
    init: function(parent) {
        this.theme_data = {};
        this.selected_theme = {};
        this.themes_by_id = {};
        return this._super.apply(this, arguments);
    },
    willStart: function() {
        var self = this;
        var get_them_data = rpc.query({
            model: 'theme.config',
            method: 'search_read',
            args: []
        });
        session.user_has_group('multicolor_backend_theme.multicolor_theme_manager_access').then(hasGroup => {
            this.administrator = hasGroup;
        });
        return $.when(get_them_data).then(function(theme_data) {
            self.theme_data = theme_data;
            for (var i in theme_data) {
                if (theme_data[i].theme_active == true) {
                    self.selected_theme = theme_data[i];
                    selected_theme = theme_data[i];
                }
                self.themes_by_id[theme_data[i].id] = theme_data[i];
            }
            if (!self.selected_theme) {
                self.selected_theme = theme_data[0];
            }
        });
    },
    //load default theme
    _loadDefaults: function() {
        var self = this;
        var item_theme = ''
        var theme = ''
        if (self.themes_by_id[$('.theme_select').val()] != undefined) {
            item_theme = self.themes_by_id[$('.theme_select').val()]
        }
        self.active_theme = item_theme
        var color_el = [
            'theme_main_color',
            'theme_font_color',
            'view_font_color'
        ];
        for (var color in color_el) {
            var el_color = self.selected_theme[color_el[color]];
            $('#' + color_el[color]).loads({
                layout: 'hex',
                flat: false,
                enableAlpha: false,
                color: el_color,
                onSubmit: function(ev) {
                    var el_id = $(ev.el).attr('id');
                    $('#' + el_id).css('background-color', '#' + ev.hex);
                    $('#' + el_id).val("#" + ev.hex);
                    $('#' + el_id).hides();
                    self._onchangeColor($(ev.el), ev.hex);
                },

                onLoaded: function(ev) {
                    $('.picker').css('color', 'green');
                },
                onChange: function(ev) {
                    var el_id = $(ev.el).attr('id');
                    $('#' + el_id).setColor(ev.hex, false);
                    $('.picker').css('color', 'red');
                }
            });
        }
        return;
    },
    //function to edit the name
    _onNameEdit: function() {
        $('.row.name #name').removeAttr('readonly');
        $('.row.name #name').css('background-color', 'rgb(238, 250, 239)');
    },
    //function for saving the name and theme
    _onNameSave: function() {
        var name_inp = $('.row.name input#name').val().trim();
        if (this.themes_by_id[$('.theme_select').val()].theme_active == true) {
            this.selected_theme.name = name_inp;
        }
        this.themes_by_id[$('.theme_select').val()].name = name_inp;
        rpc.query({
            model: 'theme.config',
            method: 'write',
            args: [
                parseInt($('.theme_select').val()),
                {
                    'name': name_inp
                }
            ]
        }).then(function() {
            $('.button-apply.fa-check').css('color', 'green');
            themes_to_update[$('.theme_select').val()] = true;
        });
        $('.row.name #name').attr('readonly', 'readonly');
        $('.row.name #name').css('background-color', 'white');
        $('.row.name i').replaceWith(
            "<i class='fa fa-pencil'/>"
        );
        $('option#' + $('.theme_select').val()).text(name_inp);
    },
    _onNameChange: function() {
        $('.button-apply.fa-check').css('color', 'red');
        delete themes_to_update[$('.theme_select').val()];
        var name_inp = $('.row.name input#name').val().trim();
        if (name_inp && (this.themes_by_id[$('.theme_select').val()].name != name_inp)) {
            $('.row.name i').replaceWith(
                "<i class='fa fa-check'/>"
            );
        }
    },
    // click function for color select
    _colorPick: function(){
    this._loadDefaults();
    },

    // function for selecting theme from the selection
    _onThemeSelectorClick: function() {
        this._loadDefaults();
        $('.themes_selector').toggleClass('show');
        $('.row.name #name').attr('readonly', 'readonly');
        $('.row.name #name').css('background-color', 'white');
    },
    // function for customizing the color
    _onchangeColor: function(element, data) {
        var $apply = $('.button-apply.fa-check');
        var current_theme = this.themes_by_id[$('.theme_select').val()];
        if ('#' + data != current_theme[element.attr('id')]) {
            $apply.css('color', 'red');
            current_theme[element.attr('id')] = '#' + data;
            this.themes_by_id[current_theme.id][element.attr('id')] = '#' + data;
            var el_id = element.attr('id');
            var vals = {
                'theme_id': current_theme.id,
                'key': el_id,
                'value': data
            };
            rpc.query({
                model: 'theme.config',
                method: 'update_color',
                args: [vals]
            }).then(function() {
                $apply.css('color', 'green');
            });
        }
        return;
    },
    //  theme change function
    _onThemeClick: function() {
        var $theme_el = QWeb.render(
            'multicolor_backend_theme.selected_theme', {
                widget: {
                    selected_theme: this.themes_by_id[$('.theme_select').val()]
                }
            });
        $('div.theme_data').replaceWith($($theme_el));
        this._loadDefaults();
        if (themes_to_update[$('.theme_select').val()] == true) {
            $('.button-apply.fa-check').css('color', 'green');
        } else {
            $('.button-apply.fa-check').css('color', '#4c4c4c');
        }
    },
    // create new theme
    _onThemeCreate: function() {
        var self = this;
        rpc.query({
            model: 'theme.config',
            method: 'create_new_theme'
        }).then(function(result) {
            self._updateThemeData(result[1]);
            var theme_el = QWeb.render(
                'multicolor_backend_theme.selected_theme', {
                    widget: {
                        selected_theme: self.themes_by_id[result[0]]
                    }
                });
            $('div.theme_data').replaceWith($(theme_el));

            var opt_el = "<option value='" + result[0] + "' >" +
                self.themes_by_id[result[0]].name + "</option>";
            $('.theme_select').append($(opt_el));
            $('.theme_select').val(result[0]);
            self._loadDefaults();
        });
    },
    // remove the theme from the inactive themes
    _onThemeRemove: function() {
        var self = this;
        var curr_theme = $('.theme_select').val();
        var theme_rec = this.themes_by_id[curr_theme];
        if (theme_rec.theme_active == true) {
            alert("You cannot delete an active theme.")
        } else {
            rpc.query({
                model: 'theme.config',
                method: 'check_for_removal',
                args: [curr_theme]
            }).then(function(theme_data) {
                if (theme_data) {
                    self._updateThemeData(theme_data);
                    var theme_el = QWeb.render(
                        'multicolor_backend_theme.selected_theme', {
                            widget: self
                        });
                    $('div.theme_data').replaceWith($(theme_el));
                    $(".theme_select option[value='" + theme_rec.id + "']").remove();
                    $(".theme_select").val(self.selected_theme.id);
                    self._loadDefaults();
                }
            });
        }
    },
    // apply the selected theme and make it active
    _onThemeApply: function() {
        var curr_theme_id = $('.theme_select').val();
        rpc.query({
            model: 'theme.config',
            method: 'update_active_theme',
            args: [curr_theme_id]
        }).then(function() {
            window.location.reload();
        });
    },
    //For updating the theme
    _updateThemeData: function(theme_data) {
        this.themes_by_id = {};
        this.theme_data = theme_data;
        for (var theme in theme_data) {
            this.themes_by_id[theme_data[theme].id] = theme_data[theme];
        }
        return;
    },
    // apply the selected theme
    _apply_theme: function() {
        if (this.selected_theme) {
            document.documentElement.style.setProperty("--theme_main_color", this.selected_theme.theme_main_color);
            document.documentElement.style.setProperty("--theme_font_color", this.selected_theme.theme_font_color);
            document.documentElement.style.setProperty("--view_font_color", this.selected_theme.view_font_color);
            $('.cybro-main-menu .input-group-text').css({
                'background-color': this.selected_theme.theme_main_color,
                'border-color': this.selected_theme.theme_main_color,
                'color': this.selected_theme.theme_font_color,
            });
            $('.o_loading').css({
                'background-color': this.selected_theme.theme_main_color,
                'color': this.selected_theme.theme_font_color,
            });
            $('.btn-primary').css({
                'background-color': this.selected_theme.theme_main_color,
                'color': this.selected_theme.theme_font_color,
            });
        }
    },
});
patch(Discuss.prototype, 'multicolor_backend_theme/static/src/js/systray_theme_menu.js', {
    _onDiscussItemClicked: function(ev) {
        this._super(ev);
        this.$('.o_mail_discuss_title_main').css({
            'box-shadow': 'none',
        });
        this.$('.o_mail_discuss_title_main.o_active').css({
            'box-shadow': 'inset 3px 0 0 ' + selected_theme.theme_main_color,
        });
    },
    _renderSidebar: function(options) {
        var res = this._super(options);
        res.find('.o_mail_discuss_title_main').css({
            'box-shadow': 'none',
        });
        res.find('.o_mail_discuss_title_main.o_active').css({
            'box-shadow': 'inset 3px 0 0 ' + selected_theme.theme_main_color,
        });
        return res;
    },
});
// add the brush icon into systray
SystrayMenu.Items.push(Temple);
patch(ControlPanel.prototype, 'multicolor_backend_theme/static/src/js/systray_theme_menu.js', {
    _update_search_view: function(searchview, isHidden, groupable, enableTimeRangeMenu) {
        this._super(searchview, isHidden, groupable, enableTimeRangeMenu);
        if (selected_theme) {
            this.$('span.o_searchview_more').css({
                background: selected_theme.theme_main_color,
                color: selected_theme.theme_font_color
            });
            document.documentElement.style.setProperty("--theme_main_color", this.selected_theme.theme_main_color);
            this.$('.o_searchview .o_searchview_facet .o_searchview_facet_label').css({
                'background-color': selected_theme.theme_main_color
            });
            this.$('.o_searchview .o_searchview_input_container .o_searchview_facet .o_searchview_facet_label').css({
                'color': selected_theme.theme_font_color
            });
            // button properties
            this.$('.btn-primary').css({
                'background-color': selected_theme.theme_main_color,
                'border-color': selected_theme.theme_main_color,
                'color': selected_theme.theme_font_color
            });
            this.$('.btn-primary:hover').css({
                'background-color': selected_theme.theme_main_color,
                'border-color': selected_theme.theme_main_color,
                'color': selected_theme.theme_font_color
            });
        }
    },
    update: function(status, options) {
        this._super(status, options);
        this.$('button.o_dropdown_toggler_btn.btn.btn-secondary.dropdown-toggle').css({
            'background-color': selected_theme.theme_main_color,
            'border-color': selected_theme.theme_main_color,
            'color': selected_theme.theme_font_color
        });
    },
    /**
     * Private function that renders a breadcrumbs' li Jquery element
     */
    _render_breadcrumbs_li: function(bc, index, length) {
        var $bc = this._super(bc, index, length);
        $bc.find('a').css({
            'color': selected_theme.view_font_color
        });
        return $bc;
    }
});
// apply theme colors in form view
FormRenderer.include({
    _renderTagSheet: function(node) {
        var sheet = this._super(node);
        sheet.find('.fa, .o_stat_value').css(
            'color', selected_theme.view_font_color);
        return sheet;
    },
    _renderHeaderButtons: function(node) {
        var buttons_obj = this._super(node);
        buttons_obj.find('.btn-primary').css({
            'background-color': selected_theme.theme_main_color,
            'border-color': selected_theme.theme_main_color,
            'color': selected_theme.theme_font_color
        });
        buttons_obj.find('.btn-primary:hover').css({
            'background-color': selected_theme.theme_main_color,
            'border-color': selected_theme.theme_main_color,
            'color': selected_theme.theme_font_color
        });
        return buttons_obj;
    },
    _renderTagHeader: function(node) {
        var statusbar_el = this._super(node);
        statusbar_el.find('button.btn.o_arrow_button.btn-primary.disabled').css({
            'color': selected_theme.view_font_color
        });
        return statusbar_el;
    },
    _renderTagForm: function(node) {
        var $res = this._super(node);
        $res.find('a').css(
            'color', selected_theme.view_font_color);
        $res.find('.o_field_widget.o_field_many2one .o_external_button').css(
            'color', selected_theme.view_font_color);
        $res.find('.btn-primary').css(
            'background-color', selected_theme.theme_main_color);
        $res.find('.btn-primary').css(
            'color', selected_theme.theme_font_color);
        return $res;
    },
});
// apply changes in listview
ListRenderer.include({
    setRowMode: function(recordID, mode) {
        var self = this;
        return this._super(recordID, mode).then(function() {
            self.$('.o_external_button').css('color', selected_theme.view_font_color);
        });
    }
});
// apply theme changes in kanban view
KanbanRenderer.include({
    _renderView: function() {
        return this._super().then(function() {
            $('.btn-primary').css('background-color',
                selected_theme.theme_main_color);
            $('.btn-primary').css('color',
                selected_theme.theme_font_color);
        });
    }
});
KanbanRecord.include({
    _render: function() {
        var self = this;
        return this._super().then(function() {
            self.$el.find('.o_kanban_image_fill_left.d-none.d-md-block').css({
                'border': '2px solid ' + selected_theme.theme_main_color
            });
            self.$el.find('.o_field_widget.badge.badge-primary').css({
                'background': selected_theme.theme_main_color
            });
        });
    }
});
// change the theme of the dropdown menus according to the current theme
patch(DropdownMenu.prototype, 'multicolor_backend_theme/static/src/js/systray_theme_menu.js', {
    _renderMenuItems: function() {
        this._super();
        if (selected_theme) {
            $('span.o_searchview_more').css({
                background: selected_theme.theme_main_color,
                color: selected_theme.theme_font_color
            });
            $('.o_searchview .o_searchview_facet .o_searchview_facet_label').css({
                'background-color': selected_theme.theme_main_color
            });
            $('.o_searchview .o_searchview_input_container .o_searchview_facet .o_searchview_facet_label').css({
                'color': selected_theme.theme_font_color
            });
        }
    },
});
// change the theme of the onboarding panel according to the current theme
patch(AbstractController.prototype, 'multicolor_backend_theme/static/src/js/systray_theme_menu.js', {
    _renderBanner: function() {
        var self = this;
        return this._super().then(function() {
            if (selected_theme) {
                self.$('.o_onboarding_wrap').css({
                    'background-color': selected_theme.theme_main_color
                });
                var color_val = 'color:' +
                    selected_theme.theme_font_color +
                    ' !important;';
                self.$('.o_onboarding_wrap a,.o_onboarding_wrap p').attr(
                    'style', color_val
                );
            }
        });
    },
});
return Temple;
