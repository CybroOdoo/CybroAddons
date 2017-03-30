odoo.define('progress_bar_color.ProgressBar', function (require) {
"use strict";

var core = require('web.core');
var utils = require('web.utils');
var Widget = require('web.Widget');
var ProgressBar = require('web.ProgressBar')
var Model = require('web.DataModel');

var QWeb = core.qweb;
var _t = core._t;


ProgressBar.include({

    _render_value: function(v) {
        var self = this
        var value = this.value;
        var max_value = this.max_value;
        if(!isNaN(v)) {
            if(this.edit_max_value) {
                max_value = v;
            } else {
                value = v;
            }
        }
        value = value || 0;
        max_value = max_value || 0;

        var widthComplete;
        if(value <= max_value) {
            widthComplete = value/max_value * 100;
        } else {
            widthComplete = max_value/value * 100;
        }
        var Users = new Model('set.progressbar.color');
        Users.call('assign_progress_bar_color', [[]]).then(function (result) {
            if (result[0]){
                for (var ranges = 0; ranges < result.length; ranges++){
                    self.$('.o_progress').toggleClass('o_progress_overflow', value > max_value);
                    if (widthComplete >= result[ranges][0] && widthComplete <= result[ranges][1]){
                        console.log(widthComplete)
                        self.$('.o_progressbar_complete').toggleClass('o_progress_red', result[ranges][2] == 'red').css('width', widthComplete + '%');
                        self.$('.o_progressbar_complete').toggleClass('o_progress_pink', result[ranges][2] == 'pink').css('width', widthComplete + '%');
                        self.$('.o_progressbar_complete').toggleClass('o_progress_orange', result[ranges][2] == 'orange').css('width', widthComplete + '%');
                        self.$('.o_progressbar_complete').toggleClass('o_progress_yellow', result[ranges][2] == 'yellow').css('width', widthComplete + '%');
                        self.$('.o_progressbar_complete').toggleClass('o_progress_light_green', result[ranges][2] == 'light_green').css('width', widthComplete + '%');
                        self.$('.o_progressbar_complete').toggleClass('o_progress_green', result[ranges][2] == 'green').css('width', widthComplete + '%');
                        self.$('.o_progressbar_complete').toggleClass('o_progress_grey', result[ranges][2] == 'grey').css('width', widthComplete + '%');
                        self.$('.o_progressbar_complete').toggleClass('o_progress_blue', result[ranges][2] == 'blue').css('width', widthComplete + '%');
                        self.$('.o_progressbar_complete').toggleClass('o_progress_purple', result[ranges][2] == 'purple').css('width', widthComplete + '%');
                        self.$('.o_progressbar_complete').toggleClass('o_progress_black', result[ranges][2] == 'black').css('width', widthComplete + '%');
                        self.$('.o_progressbar_complete').toggleClass('o_progress_brown', result[ranges][2] == 'brown').css('width', widthComplete + '%');

                        break;
                    }
                    else if (ranges == (result.length - 1)){
                        self.$('.o_progressbar_complete').toggleClass('o_progress_grey', widthComplete != 0).css('width', widthComplete + '%');
                    }

                }
            }
            else{
                self.$('.o_progress').toggleClass('o_progress_overflow', value > max_value);
                self.$('.o_progressbar_complete').toggleClass('o_progress_gt_fty', widthComplete > 50).css('width', widthComplete + '%');
                self.$('.o_progressbar_complete').toggleClass('o_progress_lt_fty', widthComplete <= 50).css('width', widthComplete + '%');
            }
        });

        if(this.readonly) {
            if(max_value !== 100) {
                this.$('.o_progressbar_value').html(utils.human_number(value) + " / " + utils.human_number(max_value));
            } else {
                this.$('.o_progressbar_value').html(utils.human_number(value) + "%");
            }
        } else if(isNaN(v)) {
            this.$('.o_progressbar_value').val(this.edit_max_value ? max_value : value);
        }
    }
});


});
