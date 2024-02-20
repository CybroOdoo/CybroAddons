/** @odoo-module **/

var PublicWidget = require('web.public.widget');
var core = require('web.core');

PublicWidget.registry.eco_banner = PublicWidget.Widget.extend({
    selector: '.eco-banner',
    disabledInEditableMode: false,

    start: function () {
        this._super.apply(this, arguments);
        this.onSlider();
    },

    onSlider: function () {
        var self = this;
//        var $slider = this.$el.find('.my-slider');
        var SLIDER_TIMEOUT = 5000;
        var owl = this.$el.find('.owl-theme1');

        function setAnimation(elems, animationType) {
            var animationEndEvent = 'webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend';
            elems.each(function () {
                var $elem = $(this);
                var animationClass = 'animated ' + $elem.data('animation-' + animationType);
                $elem.addClass(animationClass).one(animationEndEvent, function () {
                    $elem.removeClass(animationClass);
                });
            });
        }

        function initSlider(slider) {
            slider.owlCarousel({
                items: 1,
                nav: false,
                dots: false,
                autoplay: true,
                autoplayTimeout: SLIDER_TIMEOUT,
                autoplayHoverPause: false,
                loop: true,
                onInitialized: function ({ target }) {
                    var animationStyle = '-webkit-animation-duration:' + SLIDER_TIMEOUT + 'ms;animation-duration:' + SLIDER_TIMEOUT + 'ms';
                    var progressBar = $('<div class="slider-progress-bar"><span class="progress" style="' + animationStyle + '"></span></div>');
                    $(target).append(progressBar);
                },
                onChanged: function ({ type, target }) {
                    if (type === 'changed') {
                        var $progressBar = $(target).find('.slider-progress-bar');
                        var clonedProgressBar = $progressBar.clone(true);
                        $progressBar.remove();
                        $(target).append(clonedProgressBar);
                    }
                }
            });

            slider.on('change.owl.carousel', function (event) {
                var $currentItem = $('.owl-item', owl).eq(event.item.index);
                var $elemsToanim = $currentItem.find("[data-animation-out]");
                setAnimation($elemsToanim, 'out');
            });

            slider.on('changed.owl.carousel', function (event) {
                var $currentItem = $('.owl-item', owl).eq(event.item.index);
                var $elemsToanim = $currentItem.find("[data-animation-in]");
                setAnimation($elemsToanim, 'in');
            });
        }

        initSlider(owl);
    },

    destroy: function () {
        this._clearContent();
        this._super.apply(this, arguments);
    },

    _clearContent: function () {
        var $templateArea = this.$el.find('.eco-banner');
        this.trigger_up('widgets_stop_request', {
            $target: $templateArea
        });
        $templateArea.html('');
    },
});
