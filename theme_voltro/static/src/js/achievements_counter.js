import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class AchievementsCounter extends Interaction {
    static selector = ".number[data-target]";

    start() {
        // Restore the original text when stopped (e.g. in edit mode) so the
        // animated value is never saved into the page.
        const originalText = this.el.textContent;
        this.registerCleanup(() => {
            this.el.textContent = originalText;
        });
        this.target = Number(this.el.dataset.target);
        if (!Number.isFinite(this.target)) {
            return;
        }
        if ("IntersectionObserver" in window) {
            this.observer = new IntersectionObserver((entries) => {
                if (entries.some((entry) => entry.isIntersecting)) {
                    this.animate();
                }
            });
            this.observer.observe(this.el);
        } else {
            this.animate();
        }
    }

    destroy() {
        this.observer?.disconnect();
        window.cancelAnimationFrame(this.animationFrame);
    }

    animate() {
        if (this.observer) {
            this.observer.disconnect();
            this.observer = null;
        }
        const startTime = performance.now();
        const duration = 1000;
        const update = (time) => {
            const progress = Math.min((time - startTime) / duration, 1);
            this.el.textContent = `${(this.target * progress).toFixed(1)}k`;
            if (progress < 1) {
                this.animationFrame = window.requestAnimationFrame(update);
            }
        };
        this.animationFrame = window.requestAnimationFrame(update);
    }
}

registry.category("public.interactions").add("theme_voltro.achievements_counter", AchievementsCounter);
