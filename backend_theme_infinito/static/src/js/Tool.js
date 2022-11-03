odoo.define('backend_theme_infinito.Tools', function (require) {
"use strict";

    var Widget = require('backend_theme_infinito.ThemeStudioWidget');

    var Tool = Widget.extend({
        options: ['color', 'font-family', 'font-size', 'font-style', 'width', 'height',
         'border', 'padding', 'shadow', 'align'],
        remove: ['--',],

        init: function (parent, object) {
            this._super.apply(this, arguments);
            this.object = object;
        },

        start: function () {
            this.render();
        },

        render: function () {
            if (this.object && !this.tool) {
                var style = getStyle(this.object[0].dataset.class, this.options, this.remove);
                this.tool = style;
                return style;
            } else {
                return this.tool;
            }
        },
    });

    function componentToHex(c) {
       c = parseInt(c);
      var hex = c.toString(16);
      return hex.length == 1 ? "0" + hex : hex;
    }

    function rgbToHex(r, g, b) {
      return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
    }

    function getStyle(className, allowed, remove) {
        var rules = window.getComputedStyle($('.' + className)[0]);
        var rules_list = [];
        var rules_value = [];
        for (var rule of rules) {
            var alw = allowed.some(w => rule.includes(w));
            var rmv = remove.some(w => rule.includes(w));
            var exist = rules_list.some(w => w === rule);
            if (!exist && !rmv) {
                rules_list.push(rule);
                rules_value.push(rules[rule]);
            }
        }
        return rules_list.map(function (rule, index) {
            if (rule.includes('color')) {
                var color = rules_value[index] != undefined ? rules_value[index] : '#000000';
                if (color.includes('rgb') && color.match(/\d+/g) !== null) {
                    var rgb = color.match(/\d+/g);
                    var hex = rgbToHex(rgb[0], rgb[1], rgb[2]);
                    var value = hex;
                } else {
                    var value = color;
                }
//                return '<div>' + rule + ': <input type="color" name="' + rule + '" value="' + value + '"><br/></div>';
                  return [rule, 'color', value]
            } else if (rules_value[index].includes('px')) {
//                return '<div>' + rule + ': <input type="text" name="' + rule + '" value="' + rules_value[index] + '"><br/></div>';
                  return [rule, 'range', rules_value[index]]
            } else {
                return [rule, 'text', rules_value[index]]
            }

        });
    }

    function isAllowed(rule, allowed) {
        var result = allowed.any(w => rule.includes(w));
    }

    return Tool;

});