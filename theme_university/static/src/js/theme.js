/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

// ===== 1. Scroll-reveal animation Widget =====
publicWidget.registry.ThemeUniversityScrollReveal = publicWidget.Widget.extend({
    selector: ".reveal",
    start() {
        if (window.top !== window.self) {
            this.el.classList.add("revealed");
            return this._super.apply(this, arguments);
        }
        if (typeof IntersectionObserver !== "undefined") {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        setTimeout(() => entry.target.classList.add("revealed"), 80);
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
            observer.observe(this.el);
        } else {
            this.el.classList.add("revealed");
        }
        return this._super.apply(this, arguments);
    }
});

// ===== 2. Fixed Header & Topbar Visibility Offset =====
publicWidget.registry.ThemeUniversityHeaderOffset = publicWidget.Widget.extend({
    selector: ".site-header",
    start() {
        this.topbar = this.el.querySelector('.topbar');
        this.navMenu = this.el.querySelector('#navMenu');
        this._updateHeaderOffset = this._updateHeaderOffset.bind(this);
        this._updateTopbarVisibility = this._updateTopbarVisibility.bind(this);

        this._updateHeaderOffset();
        this._updateTopbarVisibility();

        window.addEventListener('scroll', this._updateTopbarVisibility, { passive: true });
        window.addEventListener('resize', this._updateHeaderOffset, { passive: true });

        if (this.navMenu) {
            this.navMenu.addEventListener('shown.bs.collapse', this._updateHeaderOffset);
            this.navMenu.addEventListener('hidden.bs.collapse', this._updateHeaderOffset);
        }

        // Active State logic
        const currentPage = window.location.pathname.split('/').pop() || 'index.html';
        const academicsPages = ['academics', 'undergraduate', 'graduate', 'online-learning', 'research-centers'];
        const campusLifePages = ['campus-life', 'housing-dining', 'clubs-orgs', 'athletics', 'health-wellness'];

        const currentLink = this.el.querySelector(`[data-nav-page="${currentPage}"]`);
        if (currentLink) {
            currentLink.classList.add('active');
        } else {
            const pathParts = window.location.pathname.split('/');
            const firstPart = pathParts[1] || '';
            const secondPart = pathParts[2] || '';
            if (academicsPages.includes(firstPart) || academicsPages.includes(secondPart)) {
                this.el.querySelector('[data-nav-section="academics"]')?.classList.add('active');
            } else if (campusLifePages.includes(firstPart) || campusLifePages.includes(secondPart)) {
                this.el.querySelector('[data-nav-section="campus-life"]')?.classList.add('active');
            }
        }

        return this._super.apply(this, arguments);
    },
    destroy() {
        window.removeEventListener('scroll', this._updateTopbarVisibility);
        window.removeEventListener('resize', this._updateHeaderOffset);
        this._super.apply(this, arguments);
    },
    _updateHeaderOffset() {
        if (this.topbar) {
            this.el.style.setProperty('--topbar-height', `${this.topbar.offsetHeight}px`);
        }
        document.body.style.paddingTop = `${this.el.offsetHeight}px`;
    },
    _updateTopbarVisibility() {
        this.el.classList.toggle('topbar-hidden', window.scrollY > 80);
        this._updateHeaderOffset();
    }
});

// ===== 3. Navbar Shrink & Shadow on Scroll =====
publicWidget.registry.ThemeUniversityNavbarScroll = publicWidget.Widget.extend({
    selector: "#mainNavbar",
    start() {
        const onScroll = () => {
            this.el.classList.toggle("scrolled", window.scrollY > 60);
        };
        window.addEventListener("scroll", onScroll, { passive: true });
        onScroll();
        return this._super.apply(this, arguments);
    }
});

// ===== 4. Back to Top Button Widget =====
publicWidget.registry.ThemeUniversityBackToTop = publicWidget.Widget.extend({
    selector: "#backToTop",
    events: {
        'click': '_onClick',
    },
    start() {
        const onScroll = () => {
            this.el.classList.toggle("visible", window.scrollY > 500);
        };
        window.addEventListener("scroll", onScroll, { passive: true });
        onScroll();
        return this._super.apply(this, arguments);
    },
    _onClick(e) {
        e.preventDefault();
        window.scrollTo({ top: 0, behavior: "smooth" });
    }
});

// ===== 5. Program Filter Tabs Widget =====
publicWidget.registry.ThemeUniversityProgramFilter = publicWidget.Widget.extend({
    selector: "#programFilterTabs",
    events: {
        'click .nav-link': '_onTabClick',
    },
    start() {
        this.grid = document.getElementById('programGrid');
        this.countEl = document.getElementById('programCount');
        this.emptyEl = document.getElementById('programEmpty');
        return this._super.apply(this, arguments);
    },
    _onTabClick(e) {
        const btn = e.currentTarget;
        const tabs = this.el.querySelectorAll('.nav-link');
        tabs.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const filter = btn.dataset.filter;
        if (!this.grid) return;

        const items = this.grid.querySelectorAll('.program-item');
        let visible = 0;

        items.forEach(item => {
            const cat = item.dataset.category;
            const show = filter === 'all' || cat === filter;
            if (!show) {
                item.classList.add('hiding');
            }
        });

        setTimeout(() => {
            items.forEach(item => {
                const cat = item.dataset.category;
                const show = filter === 'all' || cat === filter;
                if (show) {
                    item.classList.remove('hiding', 'hidden');
                    visible++;
                } else {
                    item.classList.add('hidden');
                    item.classList.remove('hiding');
                }
            });

            const currentVisible = Array.from(items).filter(i => !i.classList.contains('hidden')).length;
            if (this.countEl) this.countEl.textContent = currentVisible;
            if (this.emptyEl) this.emptyEl.classList.toggle('d-none', currentVisible > 0);
        }, 320);
    }
});

// ===== 6. Stats Section Counter Animations =====
publicWidget.registry.ThemeUniversityCounters = publicWidget.Widget.extend({
    selector: ".stat-num",
    start() {
        if (typeof IntersectionObserver !== "undefined") {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        this._animate();
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.5 });
            observer.observe(this.el);
        } else {
            this._animate();
        }
        return this._super.apply(this, arguments);
    },
    _animate() {
        const hasDataTarget = this.el.dataset.target !== undefined;
        const raw = hasDataTarget ? this.el.dataset.target : this.el.textContent.trim();
        const target = parseInt(String(raw).replace(/[^0-9]/g, ''));
        const suffix = hasDataTarget ? '' : String(raw).replace(/[0-9,]/g, '');

        const duration = 1600;
        const start = performance.now();

        const step = (now) => {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(eased * target);
            this.el.textContent = current.toLocaleString() + suffix;
            if (progress < 1) {
                requestAnimationFrame(step);
            }
        };
        requestAnimationFrame(step);
    }
});

// ===== 7. Smooth Scroll for Hash Links =====
publicWidget.registry.ThemeUniversitySmoothScroll = publicWidget.Widget.extend({
    selector: "a[href^='#']",
    events: {
        'click': '_onClick',
    },
    _onClick(e) {
        const href = this.el.getAttribute('href');
        if (href === '#') return;
        const target = document.querySelector(href);
        if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
});
