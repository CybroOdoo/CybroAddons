/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

// ===================================================================
// Header "Get the App" Button — inject via JS (safe, no XPath needed)
// ===================================================================
publicWidget.registry.VxHeaderGetApp = publicWidget.Widget.extend({
    selector: 'header#top',
    disabledInEditableMode: true,

    start: function () {
        if (!this.el.querySelector('.vx-header-get-app')) {
            var navbar = this.el.querySelector('.navbar');
            if (navbar) {
                var container = navbar.querySelector('.container, .container-fluid');
                if (container) {
                    var btn = document.createElement('a');
                    btn.href = '/get-app';
                    btn.className = 'vx-header-get-app';
                    btn.textContent = 'Get the App';
                    container.appendChild(btn);
                }
            }
        }
        return this._super.apply(this, arguments);
    },

    destroy: function () {
        var btn = this.el.querySelector('.vx-header-get-app');
        if (btn) { btn.remove(); }
        this._super.apply(this, arguments);
    },
});

// ===================================================================
// Hero Phone Parallax — subtle parallax on hero phones on scroll
// ===================================================================
publicWidget.registry.VxHeroPhones = publicWidget.Widget.extend({
    selector: '.s_vx_hero',
    disabledInEditableMode: false,

    start: function () {
        if (!this.editableMode) {
            this._bindScroll();
        }
        return this._super.apply(this, arguments);
    },

    _bindScroll: function () {
        var self = this;
        this._onScroll = function () {
            var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            var phones = self.el.querySelector('.vx-hero-phones');
            if (phones && scrollTop < 800) {
                var offset = scrollTop * 0.08;
                phones.style.transform = 'translateY(' + offset + 'px)';
            }
        };
        window.addEventListener('scroll', this._onScroll, { passive: true });
    },

    destroy: function () {
        if (this._onScroll) {
            window.removeEventListener('scroll', this._onScroll);
        }
        this._super.apply(this, arguments);
    },
});

// ===================================================================
// Gallery Hover — fade-in on scroll using IntersectionObserver
// ===================================================================
publicWidget.registry.VxGalleryHover = publicWidget.Widget.extend({
    selector: '.s_vx_gallery',
    disabledInEditableMode: false,

    start: function () {
        if (!this.editableMode) {
            this._initIntersectionObserver();
        }
        return this._super.apply(this, arguments);
    },

    _initIntersectionObserver: function () {
        var items = this.el.querySelectorAll('.vx-gallery-phone');
        if (!items.length) return;

        this._observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, { threshold: 0.1 });

        items.forEach(function (item) {
            item.style.opacity = '0';
            item.style.transform = 'translateY(20px)';
            item.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            this._observer.observe(item);
        }.bind(this));
    },

    destroy: function () {
        if (this._observer) {
            this._observer.disconnect();
        }
        this._super.apply(this, arguments);
    },
});

// ===================================================================
// Screen Showcase 3D Tilt — perspective tilt on hover
// ===================================================================
publicWidget.registry.VxScreenShowcase = publicWidget.Widget.extend({
    selector: '.vx-screen-showcase-card',
    disabledInEditableMode: false,

    events: {
        'mousemove': '_onMouseMove',
        'mouseleave': '_onMouseLeave',
    },

    start: function () {
        this._phoneFrame = this.el.querySelector('.vx-phone-frame');
        return this._super.apply(this, arguments);
    },

    _onMouseMove: function (ev) {
        if (this.editableMode || !this._phoneFrame) return;
        var rect = this.el.getBoundingClientRect();
        var x = ev.clientX - rect.left;
        var y = ev.clientY - rect.top;
        var centerX = rect.width / 2;
        var centerY = rect.height / 2;
        var rotateY = ((x - centerX) / centerX) * -5;
        var rotateX = ((y - centerY) / centerY) * 3;
        this._phoneFrame.style.transform =
            'rotateY(' + rotateY + 'deg) rotateX(' + rotateX + 'deg) scale(1.02)';
    },

    _onMouseLeave: function () {
        if (this.editableMode || !this._phoneFrame) return;
        this._phoneFrame.style.transform = '';
    },

    destroy: function () {
        if (this._phoneFrame) {
            this._phoneFrame.style.transform = '';
        }
        this._super.apply(this, arguments);
    },
});

// ===================================================================
// Feature Section Fade In — fade in sections on scroll
// ===================================================================
publicWidget.registry.VxFadeInSection = publicWidget.Widget.extend({
    selector: '.s_vx_feature_left, .s_vx_feature_right, .s_vx_more_features',
    disabledInEditableMode: false,

    start: function () {
        if (!this.editableMode) {
            this._initFadeIn();
        }
        return this._super.apply(this, arguments);
    },

    _initFadeIn: function () {
        this.el.style.opacity = '0';
        this.el.style.transform = 'translateY(30px)';
        this.el.style.transition = 'opacity 0.7s ease, transform 0.7s ease';

        this._observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, { threshold: 0.15 });

        this._observer.observe(this.el);
    },

    destroy: function () {
        if (this._observer) {
            this._observer.disconnect();
        }
        this._super.apply(this, arguments);
    },
});

// ===================================================================
// Password Toggle — show/hide password on login/signup pages
// ===================================================================
publicWidget.registry.VxPasswordToggle = publicWidget.Widget.extend({
    selector: '.vx-login-eye-btn',
    disabledInEditableMode: false,

    events: {
        'click': '_onToggle',
    },

    _onToggle: function (ev) {
        if (this.editableMode) return;
        ev.preventDefault();
        var wrap = this.el.closest('.vx-login-input-wrap');
        if (!wrap) return;
        var input = wrap.querySelector('.vx-login-input');
        var icon = this.el.querySelector('i');
        if (!input || !icon) return;

        if (input.type === 'password') {
            input.type = 'text';
            icon.classList.remove('bi-eye-slash');
            icon.classList.add('bi-eye');
        } else {
            input.type = 'password';
            icon.classList.remove('bi-eye');
            icon.classList.add('bi-eye-slash');
        }
    },

    destroy: function () {
        this._super.apply(this, arguments);
    },
});
