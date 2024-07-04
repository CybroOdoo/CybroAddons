odoo.define('weather_systray.weather', function(require) {
  "use strict";
  var core = require('web.core');
  var QWeb = core.qweb;
  var SystrayMenu = require('web.SystrayMenu');
  var Widget = require('web.Widget');
  var rpc = require('web.rpc');
/*Extending widget and adding the template*/
  var WeatherMenu = Widget.extend({
      template: 'user_weather_notification.UserMenuS',
      events: {
          'click #create_so': 'onclick_myicon',
      },
      /*when it start card is hidden*/
      start: function() {
      var self = this
      self.$('.card').hide();
      },
      /*toggle the card hide or visible*/
      onclick_myicon: async function() {
        if (self.$(".card").is(":visible")) {
            self.$('.card').hide();
        }
        else {
            self.$('.card').show();
            /*take the data from the controller and shows*/
            rpc.query({
                    route: "/weather/notification/check",
                }).then(function(result) {
                if (result.data == false){
                self.$("#description").text('Configure Settings')
                }else{
                self.$("#title").text(result.name);
                self.$("#main").text(result.weather[0].main);
                var temp = Math.floor(result.main.temp - 273);
                self.$("#temp").text(temp + "°C");
                self.$("#description").text(result.weather[0].description);
                }
               })
        }
    }
  });
  SystrayMenu.Items.push(WeatherMenu);
  return WeatherMenu;
});
