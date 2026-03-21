/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onMounted, onWillUnmount } from "@odoo/owl";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

let _cache = null;
let _orm = null;
let _currentRestrictions = null;
let _lastCashierId = null;
let _pollerInterval = null;
let _observer = null;
let _debounce = null;

function injectCSS() {
    if (document.getElementById('pos-restrictions-css')) return;
    const s = document.createElement('style');
    s.id = 'pos-restrictions-css';
    s.textContent = `
        button[data-pos-off="1"],
        button[data-pos-off="1"]:hover,
        button[data-pos-off="1"]:focus {
            opacity: 0.35 !important;
            pointer-events: none !important;
            cursor: not-allowed !important;
            filter: grayscale(60%) !important;
        }
        span[data-pos-off="1"],
        div[data-pos-off="1"] {
            opacity: 0.2 !important;
            pointer-events: none !important;
            cursor: not-allowed !important;
        }
    `;
    document.head.appendChild(s);
}

async function loadCache(orm) {
    if (_cache) return _cache;
    try {
        _cache = await orm.call('pos.session', 'get_pos_restriction_data', [[]]);
    } catch (e) {
        _cache = { employees: {}, users: {}, advanced_ids: [] };
    }
    return _cache;
}

function buildRestrictions(cashier, cache) {
    if (!cashier || !cache) return null;

    const empKey = String(cashier.id);
    const advancedIds = cache.advanced_ids || [];

    if (advancedIds.includes(empKey)) return null;

    const userKey = String(cashier.user_id?.id || cashier.user_id || '');
    const data = cache.employees?.[empKey] || cache.users?.[userKey] || null;

    if (!data) return null;

    return {
        allowNumpad:            data.pos_allow_numpad            !== false,
        allowPayments:          data.pos_allow_payments          !== false,
        allowDiscount:          data.pos_allow_discount          !== false,
        allowQty:               data.pos_allow_qty               !== false,
        allowPriceEdit:         data.pos_allow_price_edit        !== false,
        allowRemoveOrderLine:   data.pos_allow_remove_order_line !== false,
        allowCustomerSelection: data.pos_allow_customer_selection !== false,
        allowPlusMinus:         data.pos_allow_plus_minus        !== false,
    };
}

function findByText(root, textList) {
    const found = [];
    root.querySelectorAll('button').forEach(btn => {
        const t = btn.textContent.trim();
        if (textList.includes(t)) found.push(btn);
    });
    return found;
}

function markElements(elements, disabled) {
    elements.forEach(el => {
        if (disabled) {
            el.setAttribute('data-pos-off', '1');
        } else {
            el.removeAttribute('data-pos-off');
        }
    });
}

function clearAllRestrictions(root) {
    root.querySelectorAll('[data-pos-off]').forEach(el => el.removeAttribute('data-pos-off'));
}

function applyRestrictions(r) {
    const productScreen = document.querySelector('.product-screen, [class*="product-screen"]');
    const paymentScreen = document.querySelector('.payment-screen, [class*="payment-screen"]');
    const root = productScreen || paymentScreen || document.querySelector('.pos') || document.body;

    const onLoginScreen = !!document.querySelector('.login-screen, [class*="login-screen"]');
    if (onLoginScreen && !productScreen && !paymentScreen) return;

    if (!r) {
        clearAllRestrictions(root);
        return;
    }

    markElements(findByText(root, ['0','1','2','3','4','5','6','7','8','9','.']), !r.allowNumpad);
    markElements(findByText(root, ['Qty', 'QTY']),          !r.allowQty);
    markElements(findByText(root, ['%', '% Disc', 'Disc']), !r.allowDiscount);
    markElements(findByText(root, ['Price', 'PRICE']),      !r.allowPriceEdit);
    markElements(findByText(root, ['+/-', '+/−', '±']),     !r.allowPlusMinus);
    markElements(findByText(root, ['Customer']),             !r.allowCustomerSelection);

    // Also restrict Customer button on payment screen if it is active
    const payScreen = document.querySelector('.payment-screen, [class*="payment-screen"]');
    if (payScreen && payScreen !== root) {
        markElements(findByText(payScreen, ['Customer']), !r.allowCustomerSelection);
    }

    const removeSelectors = [
        '.order-line .delete', '.orderline .delete',
        '.order-line .o_delete', '.orderline .o_delete',
        '[class*="order-line"] [class*="delete"]',
        '[class*="orderline"] [class*="delete"]',
        '[class*="order-line"] [class*="remove"]',
    ];
    removeSelectors.forEach(sel => {
        try {
            root.querySelectorAll(sel).forEach(el => {
                if (!r.allowRemoveOrderLine) {
                    el.setAttribute('data-pos-off', '1');
                } else {
                    el.removeAttribute('data-pos-off');
                }
            });
        } catch (_) {}
    });
}

function startObserver() {
    const target = document.querySelector('.pos') || document.body;
    if (_observer) _observer.disconnect();

    _observer = new MutationObserver(() => {
        clearTimeout(_debounce);
        _debounce = setTimeout(() => {
            if (_currentRestrictions !== undefined) {
                _observer.disconnect();
                applyRestrictions(_currentRestrictions);
                _observer.observe(target, { childList: true, subtree: true });
            }
        }, 80);
    });

    _observer.observe(target, { childList: true, subtree: true });
}

function startPoller(pos) {
    if (_pollerInterval) clearInterval(_pollerInterval);

    _pollerInterval = setInterval(async () => {
        if (!_orm) return;
        try {
            const cashier = pos.get_cashier ? pos.get_cashier() : pos.cashier;
            if (!cashier || cashier.id === _lastCashierId) return;

            _lastCashierId = cashier.id;
            const cache = await loadCache(_orm);
            _currentRestrictions = buildRestrictions(cashier, cache);
            applyRestrictions(_currentRestrictions);
        } catch (_) {}
    }, 600);
}

patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
        injectCSS();

        const orm = useService('orm');
        _orm = orm;
        const self = this;

        onMounted(async () => {
            const cache = await loadCache(orm);
            const cashier = self.pos.get_cashier ? self.pos.get_cashier() : self.pos.cashier;

            if (cashier) {
                _lastCashierId = cashier.id;
                _currentRestrictions = buildRestrictions(cashier, cache);
                applyRestrictions(_currentRestrictions);
            }

            startObserver();
            startPoller(self.pos);
        });

        onWillUnmount(() => {
            if (_observer) { _observer.disconnect(); _observer = null; }
            if (_pollerInterval) { clearInterval(_pollerInterval); _pollerInterval = null; }
            // Do NOT clear _currentRestrictions here — PaymentScreen needs it
            _lastCashierId = null;
        });
    },

    async pay() {
        if (_currentRestrictions && !_currentRestrictions.allowPayments) {
            this.notification.add('You are not allowed to process payments.', { type: 'warning' });
            return;
        }
        return super.pay(...arguments);
    },

    async showPaymentScreen() {
        if (_currentRestrictions && !_currentRestrictions.allowPayments) {
            this.notification.add('You are not allowed to process payments.', { type: 'warning' });
            return;
        }
        return super.showPaymentScreen(...arguments);
    },

    async onClickPayButton() {
        if (_currentRestrictions && !_currentRestrictions.allowPayments) {
            this.notification.add('You are not allowed to process payments.', { type: 'warning' });
            return;
        }
        return super.onClickPayButton(...arguments);
    },
});

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        injectCSS();

        const orm = useService('orm');
        const self = this;

        onMounted(async () => {
            const el = self.el;
            const cache = await loadCache(orm);
            const cashier = self.pos.get_cashier ? self.pos.get_cashier() : self.pos.cashier;
            if (cashier) {
                _currentRestrictions = buildRestrictions(cashier, cache);
                // applyRestrictions finds the payment screen by class and restricts Customer button
                applyRestrictions(_currentRestrictions);
            }
        });
    },

    async validateOrder(isForceValidate) {
        if (_currentRestrictions && !_currentRestrictions.allowPayments) {
            this.notification.add('You are not allowed to process payments.', { type: 'warning' });
            return;
        }
        return super.validateOrder(...arguments);
    },

    async validate() {
        if (_currentRestrictions && !_currentRestrictions.allowPayments) {
            this.notification.add('You are not allowed to process payments.', { type: 'warning' });
            return;
        }
        return super.validate(...arguments);
    },

    async onClickValidate() {
        if (_currentRestrictions && !_currentRestrictions.allowPayments) {
            this.notification.add('You are not allowed to process payments.', { type: 'warning' });
            return;
        }
        return super.onClickValidate(...arguments);
    },
});