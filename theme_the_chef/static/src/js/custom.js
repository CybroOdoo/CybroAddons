odoo.define('theme_the_chef.custom', function(require) {
    "use strict"
//    Function of Slider
    var PublicWidget = require('web.public.widget');
    var Slider = PublicWidget.Widget.extend({
        selector: '.banner',
        start: function() {
            var self = this;
            self.onSlider();
        },

    onSlider: function() {
        var self = this;
        this.$("#slider").owlCarousel({
            items: 1,
            loop: true,
            margin: 30,
            stagePadding: 30,
            smartSpeed: 450,
            autoplay: true,
            autoPlaySpeed: 1000,
            autoPlayTimeout: 1000,
            autoplayHoverPause: true,
            dots: false,
            nav: true,
            navText: ['<i class="fa fa-angle-left"></i>', '<i class="fa fa-angle-right"></i>']
        });

        function counter() {
            var buttons = self.$el.find('.owl-dots button');
            buttons.each(function(index, item) {
                $(item).find('span').text(index + 1);
            });
        }
        this.$("#slider2").owlCarousel({
            items: 1,
            loop: true,
            smartSpeed: 450,
            autoplay: true,
            autoPlaySpeed: 1000,
            autoPlayTimeout: 1000,
            autoplayHoverPause: true,
            onInitialized: counter,
            dots: true,
        });

        function counter() {
            var buttons = self.$el.find('.owl-dots button');
            buttons.each(function(index, item) {
                $(item).find('span').index + 1;
            });
        }

        var inputEle = document.getElementById('timeInput');

        function onTimeChange() {
            var timeSplit = inputEle.value.split(':'),
                hours,
                minutes,
                meridian;
            hours = timeSplit[0];
            minutes = timeSplit[1];
            if (hours > 12) {
                meridian = 'PM';
                hours -= 12;
            } else if (hours < 12) {
                meridian = 'AM';
                if (hours == 0) {
                    hours = 12;
                }
            } else {
                meridian = 'PM';
            }
            alert(hours + ':' + minutes + ' ' + meridian);
        }
    }
    });

    PublicWidget.registry.banner = Slider;
    return Slider;
});