odoo.define('backend_theme_infinito.VisualEditor', function (require) {
"use strict";

    var Dialog = require('web.Dialog');

    var VisualEditor = Dialog.extend({
        template: "VisualEditor",
        events: {
            'change input': '_onChangeInput',
        },
        init: function (element) {
            this.element = element;
            var options = {};
            options.title = 'Visual Editor';
            options.size = 'medium';
            var self = this;
            options.buttons = [];
            options.buttons.push({text: "Apply", classes: "btn-primary", click: function (e) {
                self._applyStyle();
            }});
            options.buttons.push({text: "Cancel", close: true});
            options.buttons.push({text: "Advanced", classes: "btn-primary", click: function (e) {
                self._openAdvanced();
            }});
            this._super(element, options);
        },
        start: function () {
            this.$el[0].append(this.element[0].cloneNode(true));
            this.preview = this.$(this.$el[0].firstChild);
            this.tools = this.$el[2];
            for (var child of this.tools.children) {
                if (child.tagName in ['INPUT', 'SELECT']) {
                    var val = this.element.css(child.id);
                    if (val && val.includes('rgb') && val.match(/\d+/g) !== null) {
                        var rgb = val.match(/\d+/g);
                        var hex = rgbToHex(rgb[0], rgb[1], rgb[2]);
                        val = hex;
                    } else if (val && val.includes('px')) {
                        val = val.replace('px', '');
                        if (val.includes(' ')) {
                            val = val.split(' ')[0];
                        }
                    }
                    if ($(child).data('unit') == '%') {
                        val = getPercentage(val);
                    }
                    $(child).val(val);
                }
            }
        },
        _onChangeInput: function (e) {
            var input = e.target;
            var value = input.value;
            if (input.dataset.unit) {
                value += input.dataset.unit;
            }
            var name = input.id;
            var add = true;
            var style = this.preview.attr('style') ? this.preview.attr('style').split(';') : [];
            if (style) {
                for (var i = 0; i < style.length; i++) {
                    var s = style[i].split(':');
                    if (s[0] == name) {
                        style[i] = `${name}: ${value}`;
                        add = false;
                        break;
                    }
                }
            }
            if(add) {
                style.push(`${name}: ${value}`);
            }
            style = style.join(';');
            this.preview.attr('style', style);
        },
        _applyStyle: function () {
            var style = this.preview.attr('style');
            this.element.attr('style', style);
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

     function getPercentage(value) {
        var screenWidth = window.screen.width;
        var perc = ( screenWidth - value ) / screenWidth;
        return perc;
    }

    return VisualEditor;

});