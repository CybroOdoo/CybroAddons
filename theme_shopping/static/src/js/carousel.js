import { Interaction } from '@web/public/interaction';

// Native scrolling keeps carousels usable with touch, keyboard and without jQuery.
export class ShoppingCarousel extends Interaction {
    setupCarousel(element, single = false) {
        if (!element) return;
        element.classList.add('st-carousel');
        element.classList.toggle('st-carousel-single', single);
        element.tabIndex = 0;
        this.carousel = element;
        if (element.children.length < 2) return;
        const controls = document.createElement('div');
        controls.className = 'st-carousel-controls';
        for (const [label, direction] of [['Previous', -1], ['Next', 1]]) {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'btn btn-outline-secondary btn-sm';
            button.textContent = label;
            button.addEventListener('click', () => this.scrollCarousel(direction));
            controls.append(button);
        }
        element.after(controls);
        this.registerCleanup(() => controls.remove());
        if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            const timer = setInterval(() => {
                if (!document.hidden && !element.matches(':hover, :focus-within')) {
                    this.scrollCarousel(1);
                }
            }, 5000);
            this.registerCleanup(() => clearInterval(timer));
        }
        this.registerCleanup(() => {
            element.classList.remove('st-carousel', 'st-carousel-single');
            element.removeAttribute('tabindex');
        });
    }

    scrollCarousel(direction) {
        const el = this.carousel;
        const atEnd = el.scrollLeft + el.clientWidth >= el.scrollWidth - 2;
        el.scrollTo({
            left: direction > 0 && atEnd ? 0 : el.scrollLeft + direction * el.clientWidth,
            behavior: 'smooth',
        });
    }
}
