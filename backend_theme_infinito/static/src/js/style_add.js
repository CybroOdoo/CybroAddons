odoo.define('backend_theme_infinito.StyleAdd', function (require) {
"use strict";

    var Dialog = require('web.Dialog');

    var StyleAdd = Dialog.extend({
        template: 'StyleAdd',
        events: _.extend({}, Dialog.events, {
            'keyup .search_property': '_onChange',
        }),
        init: function(parent, tools, current_tools) {
            var options = {};
            options.title = 'Select Property';
            options.size = 'medium';
            var self = this;
            options.buttons = [];
            options.buttons.push({text: "+", classes: "btn-primary", click: function (e) {
                self.add();
            }});
            this._super(parent, options);
            this.parent = parent;
            this.tools = tools;
            this.current_tools = current_tools;
        },

        start: function(){
            this.renderDrops('');
        },
        renderDrops: function(search){
            this.$el.find('select').html('')
            for(var tool of this.tools){
                if(!this.current_tools.includes(tool.name) && tool.name.includes(search)){
                    var content = `<option role="menuitem" href="#" data-type="${tool.type}" data-value="${tool.name}" data-default-value="" class="dropdown-item">${tool.name}</option>`;
                    this.$el.find('select').append(content);
                }
            }
        },
        _onChange: function(ev){
            this.renderDrops(ev.target.value);
        },
        add: function(){
            var val = this.$el.find('select').val();
            this.parent.current_tools.push(val);
            this.current_tools.push(val);
            var option = this.$el.find('select').find('option[data-value="' + val + '"]');
            var current = this.tools.filter(tool => tool.name == val);
            this.parent.renderNewTool(current[0]);
            this.close();
        },
    });

    return StyleAdd;

});