odoo.define('user_weather_notification.weather_card', function (require) {
    "use strict";
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    var rpc = require('web.rpc');
    /**
     * Extends Widget and adds the template for the weather card.
     */
    var ActionMenu = Widget.extend({
        template: 'user_weather_notification.UserMenuS',
        events: {
            'click #get-weather': 'OnClickGetWeather',
        },
        /**
         * Hides the card when the widget starts.
         */
        start: function () {
            var self = this;
            self.$('.card').hide();
        },
        /**
         * Toggles the visibility of the weather card.
         */
        OnClickGetWeather: async function () {
            var self = this;
            if (self.$(".card").is(":visible")) {
                self.$('.card').hide();
            } else {
                self.$('.card').show();
                // Take the data from the controller and show it
                rpc.query({
                    route: "/weather/notification/check",
                }).then(function (result) {
                    if (result.data == false) {
                        self.$("#description").text('Configure Settings');
                    } else {
                        self.$("#title").text(result.name);
                        self.$("#text").text(result.weather[0].main);
                        var temp = Math.floor(result.main.temp - 273);
                        self.$("#temperature").text(temp + "°C");
                        self.$("#description").text(result.weather[0].description);
                    }
                });
            }
        }
    });
    SystrayMenu.Items.push(ActionMenu);
    return ActionMenu;
});
