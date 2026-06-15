/** @odoo-module **/
import { whenReady } from "@odoo/owl";

whenReady(() => {
    // Target testimonials and related products carousels on product page
    const carousels = document.querySelectorAll(
        '.section-testimonials .container-slider-testimonials-products .owl-carousel, ' +
        '.section-related-products .related-products-list .owl-carousel, ' +
        '.thred-carousel, ' +
        '.blog-carousel, ' +
        '.section-all-the-snekers .owl-carousel'
    );
    if (!carousels.length) return;
    carousels.forEach((carousel) => {
        // Prefer existing owl-item wrappers; fall back to .item or direct children
        let items = carousel.querySelectorAll('.owl-item');
        if (!items.length) {
            items = carousel.querySelectorAll('.item');
        }
        if (!items.length) {
            items = carousel.children ? carousel.children : [];
        }
        if (!items || !items.length) return;
        // Mark as initialized and ensure visible
        carousel.classList.add('js-owl-slider', 'owl-loaded', 'owl-drag');
        carousel.style.display = 'block';
        // Stage wrapper
        let stage = carousel.querySelector('.owl-stage');
        if (!stage) {
            stage = document.createElement('div');
            stage.className = 'owl-stage';
            while (carousel.firstChild) {
                stage.appendChild(carousel.firstChild);
            }
        }
        // Stage outer wrapper for overflow hidden
        let stageOuter = carousel.querySelector('.owl-stage-outer');
        if (!stageOuter) {
            stageOuter = document.createElement('div');
            stageOuter.className = 'owl-stage-outer';
            carousel.appendChild(stageOuter);
        }
        if (!stage.parentElement || stage.parentElement !== stageOuter) {
            stageOuter.appendChild(stage);
        }
        // Stage styling for horizontal layout
        stage.style.transition = 'transform 0.35s ease';
        stage.style.display = 'flex';
        stage.style.gap = '20px';
        // Dots container
        let dotsContainer = carousel.querySelector('.owl-dots');
        if (!dotsContainer) {
            dotsContainer = document.createElement('div');
            dotsContainer.className = 'owl-dots';
            carousel.appendChild(dotsContainer);
        }
        // Slides per view responsive
        const getSlidesPerView = () => {
            const w = window.innerWidth;
            if (carousel.classList.contains('thred-carousel')) {
                if (w < 600) return 1;
                if (w < 1000) return 2;
                return 5;
            }
            if (carousel.closest('.section-all-the-snekers')) {
                if (w < 600) return 1;
                return 2;
            }
            if (carousel.classList.contains('blog-carousel')) {
                if (w < 768) return 1;
                return 2;
            }
            if (w < 576) return 1;
            if (w < 992) return 2;
            return 3; // desktop
        };
        let slidesPerView = getSlidesPerView();
        let currentSlide = 0;
        let totalSlides = Math.max(1, Math.ceil(items.length / slidesPerView));
        // Create dots
        dotsContainer.innerHTML = '';
        for (let i = 0; i < totalSlides; i++) {
            const dot = document.createElement('button');
            dot.className = `owl-dot ${i === 0 ? 'active' : ''}`;
            dot.innerHTML = '<span></span>';
            dot.addEventListener('click', () => {
                currentSlide = i;
                updateSlider();
                startAutoSlide(); // Restart timer on manual interaction
            });
            dotsContainer.appendChild(dot);
        }
        function getItemWidth() {
            const first = items[0];
            if (!first) return 0;
            // If we set explicit width, use it, otherwise fallback
            return first.getBoundingClientRect().width + 20;
        }
        function setItemWidths() {
            const containerWidth = carousel.getBoundingClientRect().width;
            const gap = 20;
            // Calculate width: (Container - TotalGaps) / ItemsPerView
            // TotalGaps = gap * (slidesPerView - 1)
            // But for the stride/offset calculation to work with the gap property, 
            // we usually want the item to be slightly smaller if we rely on gap.
            // However, the existing logic uses gap: 20px on flex container.
            const totalGapSpace = gap * (slidesPerView - 1);
            const itemWidth = (containerWidth - totalGapSpace) / slidesPerView;
            items.forEach(item => {
                item.style.width = `${itemWidth}px`;
                item.style.flex = `0 0 ${itemWidth}px`;
                item.style.maxWidth = `${itemWidth}px`;
            });
        }
        // Initial set
        setItemWidths();
        function updateSlider() {
            if (!items || !items.length || !stage) return;
            const w = getItemWidth();
            const offset = -currentSlide * w * slidesPerView;
            stage.style.transform = `translate3d(${offset}px, 0, 0)`;
            // Update dots for this carousel only
            carousel.querySelectorAll('.owl-dot').forEach((dot, index) => {
                dot.classList.toggle('active', index === currentSlide);
            });
        }
        // Auto-slide
        let interval;
        const startAutoSlide = () => {
            if (interval) clearInterval(interval);
            if (totalSlides > 1) {
                interval = setInterval(() => {
                    currentSlide = (currentSlide + 1) % totalSlides;
                    updateSlider();
                }, 5000);
            }
        };
        startAutoSlide();
        // Recompute on resize
        window.addEventListener('resize', () => {
            const prevSpv = slidesPerView;
            slidesPerView = getSlidesPerView();
            setItemWidths(); // Update widths on resize
            if (slidesPerView !== prevSpv) {
                totalSlides = Math.max(1, Math.ceil(items.length / slidesPerView));
                // rebuild dots
                if (dotsContainer) {
                    dotsContainer.innerHTML = '';
                    for (let i = 0; i < totalSlides; i++) {
                        const dot = document.createElement('button');
                        dot.className = `owl-dot ${i === currentSlide ? 'active' : ''}`;
                        dot.innerHTML = '<span></span>';
                        dot.addEventListener('click', () => {
                            currentSlide = i;
                            updateSlider();
                            startAutoSlide(); // Restart timer on manual interaction
                        });
                        dotsContainer.appendChild(dot);
                    }
                }
                startAutoSlide(); // Restart timer on resize
            }
            updateSlider();
        });
        updateSlider();
    });
});
