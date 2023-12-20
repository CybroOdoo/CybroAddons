odoo.define('theme_autofly.theme.js', function (require) {
    'use strict';

    var core = require('web.core');
    var Widget = require('web.Widget');
    var ajax = require('web.ajax');

    var QWeb = core.qweb;

    var AutoflyOwlComponent = Widget.extend({
        init: function (parent) {
            this._super(parent);
            this.a = 0;
        },

        start: function () {
            this.setupStickyHeader();
            this.setupOwlCarousel();
            this.setupCounterAnimation();
            return this._super.apply(this, arguments);
        },

        setupStickyHeader: function () {
            var self = this;
            var s = this.$(".sticker");
            var pos = s.position();

            this.$('#wrapwrap').scroll(function () {
                var windowpos = self.$('#wrapwrap').scrollTop();
                if ((windowpos >= pos.top) && (windowpos >= 100)) {
                    s.addClass("fadeInDown bg_white b_shadow");
                } else {
                    s.removeClass("fadeInDown bg_white b_shadow");
                }
            });
        },

        setupOwlCarousel: function () {
            this.$(".owl-theme1").owlCarousel({
                items: 3,
                loop: true,
                margin: 40,
                stagePadding: 0,
                smartSpeed: 450,
                autoplay: false,
                autoPlaySpeed: 3000,
                autoPlayTimeout: 1000,
                autoplayHoverPause: true,
                dots: false,
                nav: true,
                responsive: {
                    0: {
                        items: 1,
                        nav: false,
                    },
                    600: {
                        items: 2,
                        nav: false,
                    },
                    1000: {
                        items: 3,
                        nav: true,
                        loop: false,
                    },
                },
            });
        },

        setupCounterAnimation: function () {
            var self = this;
            this.$('#wrapwrap').scroll(function () {
                if (!self.$("#counter-box").length > 0) return;
                var oTop = self.$("#counter-box").offset().top - window.innerHeight;
                if (self.a === 0 && self.$(window).scrollTop() > oTop) {
                    self.$(".counter").each(function () {
                        var $this = self.$(this),
                            countTo = $this.attr("data-number");
                        $({
                            countNum: $this.text()
                        }).animate(
                            {
                                countNum: countTo
                            },
                            {
                                duration: 5000,
                                easing: "swing",
                                step: function () {
                                    $this.text(Math.ceil(this.countNum).toLocaleString("en"));
                                },
                                complete: function () {
                                    $this.text(Math.ceil(this.countNum).toLocaleString("en"));
                                }
                            }
                        );
                    });
                    self.a = 1;
                }
            });
        },
    });

    core.action_registry.add('autofly+_owl_component', AutoflyOwlComponent);

    return {
        MyOwlComponent: MyOwlComponent,
    };
});
