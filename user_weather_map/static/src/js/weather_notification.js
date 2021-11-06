odoo.define('user_weather_map.weather_notification', function (require) {
"use strict";

var core = require('web.core');
var SystrayMenu = require('web.SystrayMenu');
var Widget = require('web.Widget');
var Model = require('web.DataModel');
var QWeb = core.qweb;

var weather_menu = Widget.extend({
    template:'user_weather_map.weather_menu',

    events: {
        "click .dropdown-toggle": "on_click_weather_board",
        "click .fa-cog": "go_to_weather_settings",
    },

    init:function(parent, name){
        this.widget = {};
        this.reminder = null;
        this._super(parent);
    },

    render_widget: function() {
        var self = this;
        var user = self.session.uid;
        var weather = new Model('user.weather.map');
        new Model("user.weather.map").call("get_weather_data",['',user]).then(function(data){
             var weather = QWeb.render("WeatherDetails", {widget:self,
             date_now: data.date_now,
             date_weather_update: data.date_weather_update,
             name: data.name,
             city: data.city,
             user_id: data.user_id,
             weather: data.weather,
             description: data.description,
             temp: data.temp,
             pressure: data.pressure,
             humidity: data.humidity,
             min_temp: data.min_temp,
             max_temp: data.max_temp,
             issue: data.issue,
             });
            $('.weather_notification').html(weather);
        });
        },

    go_to_weather_settings: function (event) {
        var action = {
                type: 'ir.actions.act_window',
                res_model: 'user.weather.map.config',
                view_mode: 'form',
                target:'inline',
                views: [[false, 'form']],
            };
            this.do_action(action);
    },

    on_click_weather_board: function (event) {
        this.render_widget();
    },

});

SystrayMenu.Items.push(weather_menu);
});
