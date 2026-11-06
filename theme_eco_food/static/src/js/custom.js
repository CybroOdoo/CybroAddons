import { AddToCart } from "@website_sale/interactions/add_to_cart";
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class WebsiteSaleCart extends AddToCart {
    // Listen on the stable website root so Owl Carousel copies work too.
    static selector = "#wrapwrap";
    dynamicContent = {
        _root: { "t-on-click": this.onCartClick },
    };

    async onCartClick(ev) {
        const button = ev.target.closest(".cart-btn");
        if (!button) {
            return;
        }
        ev.preventDefault();
        if (this.addingToCart) {
            return;
        }
        this.addingToCart = true;
        button.setAttribute("aria-busy", "true");
        try {
            return await super.addToCart({ currentTarget: button });
        } finally {
            this.addingToCart = false;
            button.removeAttribute("aria-busy");
        }
    }
}

registry.category("public.interactions").add("theme_eco_food.add_to_cart", WebsiteSaleCart);

export class NewsletterSignup extends Interaction {
    static selector = "#newsletter";
    dynamicContent = {
        _root: { "t-on-click.prevent": this.locked(this.subscribe) },
    };

    async subscribe() {
        const footer = this.el.closest(".footer");
        const emailInput = footer.querySelector(".newsletter-email");
        const warning = footer.querySelector(".warning");
        const email = emailInput?.value.trim();
        if (!email) {
            warning.textContent = "Please enter a valid email address.";
            warning.style.display = "block";
            return;
        }
        const subscribed = await this.waitFor(rpc("/subscribe_newsletter", { email }));
        warning.textContent = subscribed
            ? "Thank you for subscribing."
            : "This email is invalid or already subscribed.";
        warning.style.color = subscribed ? "green" : "red";
        warning.style.display = "block";
        if (subscribed) {
            emailInput.value = "";
        }
    }
}

registry.category("public.interactions").add("theme_eco_food.newsletter_signup", NewsletterSignup);

export class ProductCardNavigation extends Interaction {
    // Delegate from the stable root so carousel copies retain whole-card navigation.
    static selector = "#wrapwrap";
    dynamicContent = {
        _root: {
            "t-on-click": this.onCardClick,
            "t-on-auxclick": this.onCardClick,
        },
    };

    onCardClick(ev) {
        const card = ev.target.closest(".eco-food-card-content[data-product-url]");
        if (!card || ev.defaultPrevented || ev.button > 1 ||
            ev.target.closest("a, button, input, select, textarea")) {
            return;
        }
        ev.preventDefault();
        if (ev.ctrlKey || ev.metaKey || ev.shiftKey || ev.button === 1) {
            window.open(card.dataset.productUrl, "_blank", "noopener");
        } else {
            window.location.assign(card.dataset.productUrl);
        }
    }
}

registry.category("public.interactions").add("theme_eco_food.product_card_navigation", ProductCardNavigation);
