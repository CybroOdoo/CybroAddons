odoo.define('backend_theme_infinito.theme_editor_sidebar', function (require) {
"use strict";

    var Widget = require('backend_theme_infinito.ThemeStudioWidget');
    var Tools = require('backend_theme_infinito.Tools');
    var NewTools = require('backend_theme_infinito.NewTools');
    var StyleAdd = require('backend_theme_infinito.StyleAdd');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    const { browser } = require("@web/core/browser/browser");
    var QWeb = core.qweb;
    var ThemeEditorSidebar = Widget.extend({
        template: 'theme_editor_sidebar',
        events: {
            'change #slider': '_onClickInput',
            'change #favcolor': '_onClickInput',
            'change #file': '_onClickInput',
            'change #text': '_onClickInput',
            'change #select': '_onClickInput',
            'change #presets': '_onPresetChange',
            'click .js_add_tool': '_OnAddStyle',
            'click .close_studio': '_Close',
            'click .custom .alignemet a img': 'alignText',
            'click .js_save_changes': '_onSaveChanges',
            'click .js_reset_changes': '_onResetChanges',
            'click .toggle-btn': 'toggleSidebar',
        },
        init: function (parent, object) {
            this._super.apply(this, arguments);
            this.object = object;
            this.editMode = parent.editMode;
            this.added_tools = [];
            this.current_tools = [],
            this.parent = parent;
        },
        willStart: async function(){
            this._super.apply(this, arguments);
            await ajax.jsonRpc('/theme_studio/get_presets', 'call', {})
                .then((response) => {
                    this.presets = response;
                });
        },
        start: function () {
            this._super.apply(this, arguments);
            this.$el.next().removeClass('marg_main');
            this.$el.find('#elem_name').html(this.object.data('name'))
            this.renderTools();
            this.renderPresets();
        },
        renderPresets: function(){
            if(this.object && this.object.data('preset')){
                let preset_type = this.object.data('preset')
                this.$el.find('.infinito-preset').removeClass('d-none');
                let content = '';
                for(let preset of this.presets[preset_type]){
                    content += `<option data-style='${JSON.stringify(preset.style)}'>${preset.name}</option>`
                }
                this.$el.find('.infinito-preset select').html(content);
            }
        },
        _onPresetChange: function(ev){
            let index = ev.target.selectedIndex;
            let elem = ev.target.children[index];
            let style = JSON.parse(elem.dataset.style);
            let data = [];
            let new_style = '';
            this.object.attr('style', '');
            this.$el.find('.infinito-remove').remove();
            for(let rule in style){
                new_style += `${rule}: ${style[rule]} !important;`
                data.push([rule, style[rule]]);
            }
            this.object.attr('style', new_style)
            this.renderExistingTool(data);
        },
        _Close: function() {
            this.$el.css('width', '0');
            this.$el.parent().next().css('margin-left', '0')
        },
        alignText: function(ev){
            ev.stopPropagation();
            let elem = this.$(ev.target).parent();
            this.object.attr('style', `${elem.data('type')}: ${elem.data('align')}`)
        },
        _onClickSidebarItem: function (ev) {
            var $target = $(ev.currentTarget);
        },
        renderTools: function () {
            var self = this;
            this.$('.tools').html('');
            this.tools = this.tool || new Tools(this, this.object).render();
            ajax.jsonRpc('/theme_studio/get_current_style', 'call', {
                'selector': '.'+this.object[0].dataset.class,
            }).then(function (data) {
                if(data){
                    self.renderExistingTool(data);
                }
            });
            this.saveData();
        },
        _OnAddStyle: function(){
            new StyleAdd(this, NewTools.property, this.current_tools).open();
        },
        _onSaveChanges: function(){
            var self = this;
            new Dialog(this, {
                title: "Save Changes",
                $content: QWeb.render('backend_theme_infinito.saveChanges'),
                buttons: [{text: 'Save', classes: 'btn-primary', close: true, click: async function () {
                    var styles = this.$el.find('input:checked');
                    for(var style of styles){
                        await self._onClickApply(style.name);
                    }
                    await self.setAssets();

                }}, {text: 'Discard', close: true}],
            }).open();
        },
        _onResetChanges: function(){
            this.object.attr('style', '');
            this.$el.find('.infinito-remove').remove();
            this.renderTools();
        },
        _onClickInput: function(ev){
            var input_value, new_attr = '';
            var input_type = $(ev.currentTarget).attr('name');
            var all_alts = [input_type];
            var unit = $(ev.currentTarget).data('unit');
            var alt = $(ev.currentTarget).data('alt').split(',');
            if($(ev.currentTarget).attr('type') == 'range'){
                let value = $(ev.currentTarget).val();
                if(unit){
                    value += unit;
                }
                value = $(ev.currentTarget).val() == '-1' ? 'infinite' : value;
                $(ev.currentTarget).next().html(value);
            }
            if (unit) {
                input_value = $(ev.currentTarget).val()+ unit + ' !important;';
            } else {
                input_value = $(ev.currentTarget).val() + ' !important;';
            }
            input_value = $(ev.currentTarget).val() == '-1' ? 'infinite !important;' : input_value;
            var style = input_type + ': ' + input_value;
            for (var i = 0; i < alt.length; i++){
                if (alt[i] != ''){
                    style += alt[i] + input_type + ': ' + input_value;
                    all_alts.push(alt[i] + input_type)
                }
            }
            var attr = this.object.attr('style');
            if(attr){
                attr = attr.split(';').filter(function(atr){
                    if(!all_alts.includes(atr.split(':')[0]) && atr.split(':')[0] != ''){
                        new_attr += atr + ';'
                    }
                });
            }
            this.object.attr('style', new_attr + style);
           this.object.data('style', new_attr + style);
        },
        _onClickApply: async function(data){
            var styles = this.object[0].style;
            var changed_styles = [];
            for (var i = 0; i < styles.length; i++) {
                changed_styles.push(styles[i]);
            }
            var changed_style_json = {};
            for (var i in changed_styles) {
                changed_style_json[changed_styles[i]] = styles[changed_styles[i]];
            }
            await ajax.jsonRpc('/theme_studio/save_styles', 'call', {
                'changed_styles': JSON.stringify(changed_style_json),
                'object_class': this.object[0].dataset.class,
                'hover': data == 'hover' ? true : false,
            });
        },
        renderNewTool: function(tool, val=null){
            if(tool){
                var value = this.getDefaultValue(tool.name);
                if(val){
                    value = val;
                }
                if(tool.type == 'range'){
                    value = value.replace(/[^0-9,.]+/g, "")
                }
                tool.default = value;
                var content = QWeb.render('backend_theme_infinito.'+tool.type, {
                                widget: tool,
                            });
                var elmnt = this.$el.find('.button_cutomise').append(content);
                if(tool.type == 'select'){
                    elmnt.find('select').val(value)
                }
            }
        },
        renderExistingTool: function(data){
            for(var rule of data){
                var current = NewTools.property.filter(tool => tool.name == rule[0].replace(' ', ''));
                this.current_tools.push(rule[0].replace(' ', ''));
                this.renderNewTool(current[0]);
            }
        },
        getDefaultValue: function(property){
            var val = window.getComputedStyle(this.object[0]).getPropertyValue(property);
            if(val.includes('rgb')){
                var rgb = val.match(/\d+/g);
                val = rgbToHex(rgb[0], rgb[1], rgb[2]);
            }
            return val
        },
        setAssets: function(){
            browser.location.search = "?debug=assets";
        },
        saveData: function () {
            this._super.apply(this, arguments);
        },

        toggleSidebar: function(ev){
            this.$el.toggleClass('sidebar-hider-infinito');
            this.$el.next().toggleClass('marg_main');
        }

    });

    function componentToHex(c) {
       c = parseInt(c);
      var hex = c.toString(16);
      return hex.length == 1 ? "0" + hex : hex;
    }

    function rgbToHex(r, g, b) {
      return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
    }

    return ThemeEditorSidebar;

});