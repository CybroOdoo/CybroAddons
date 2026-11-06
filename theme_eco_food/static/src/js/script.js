
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class myNavbar extends Interaction {
    static selector = '#eco_food_header';
    dynamicContent = {
        _window: { "t-on-resize": this._fixHeight },
        ".navbar-toggler": { "t-on-click": this._onToggle },
        ".overlay": { "t-on-click": this._toggleMobileMenu },
        "#pricelistDropdown": { "t-on-change": this._handlePricelistChange },
    };
    start() {
        this._fixHeight();
    }
    _onToggle() {
        this._fixHeight();
        this._toggleMobileMenu();
    }
    _fixHeight() {
        for (const menu of this.el.querySelectorAll('.navbar-nav')) {
            menu.style.maxHeight = `${document.documentElement.clientHeight}px`;
        }
    }
    _toggleMobileMenu() {
        for (const menu of this.el.querySelectorAll('.mobileMenu, .overlay')) {
            menu.classList.toggle('open');
        }
    }
    _handlePricelistChange() {
        const selectedPricelistId = this.el.querySelector('#pricelistDropdown').value;
        window.location.href = '/shop/change_pricelist/' + selectedPricelistId;
    }
}

registry.category("public.interactions").add("theme_eco_food.myNavbar", myNavbar);
