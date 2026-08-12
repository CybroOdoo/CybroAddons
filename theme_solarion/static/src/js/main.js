/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.SolarionTheme = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    
    start: function () {
        this._super.apply(this, arguments);
        this._initReveal();
        this._initCounters();
        this._initTechSteps();
        this._initFaq();
    },

    _initReveal: function () {
        const revealElements = this.el.querySelectorAll('[data-reveal="true"], .service-card, .stat-card, .testimonial-card, .pillar, .contact__info-card');
        if (!revealElements.length) return;
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-revealed', 'revealed');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
        
        revealElements.forEach(el => observer.observe(el));
    },
    
    _initCounters: function () {
        const counters = this.el.querySelectorAll('[data-count]');
        if (!counters.length) return;
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this._animateCounter(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        
        counters.forEach(el => observer.observe(el));
    },
    
    _animateCounter: function (el) {
        const target = parseInt(el.getAttribute('data-count'), 10);
        let start = 0;
        const duration = 2000;
        const step = target / (duration / 16);
        
        const animate = () => {
            start += step;
            if (start < target) {
                el.innerText = Math.floor(start).toLocaleString();
                requestAnimationFrame(animate);
            } else {
                el.innerText = target.toLocaleString();
            }
        };
        animate();
    },
    
    _initTechSteps: function () {
        const steps = this.el.querySelectorAll('.tech__step');
        if (!steps.length) return;
        
        steps.forEach(step => {
            step.addEventListener('click', () => {
                steps.forEach(s => s.classList.remove('active'));
                step.classList.add('active');
            });
        });
    },
    
    _initFaq: function () {
        const faqItems = this.el.querySelectorAll('.faq-item');
        if (!faqItems.length) return;
        
        faqItems.forEach(item => {
            const question = item.querySelector('.faq-item__q');
            if (question) {
                question.addEventListener('click', () => {
                    const isOpen = item.classList.contains('open');
                    faqItems.forEach(i => i.classList.remove('open'));
                    if (!isOpen) {
                        item.classList.add('open');
                    }
                });
            }
        });
    }
});
