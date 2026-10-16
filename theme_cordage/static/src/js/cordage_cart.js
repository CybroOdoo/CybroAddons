/* =========================================================
   CORDAGE — Odoo-integrated cart logic
   Uses Odoo's /shop/cart/update JSON-RPC endpoint.
   ========================================================= */

(function () {
    'use strict';

    /**
     * Adds a product to the cart via JSON-RPC.
     * @param {string|number} productId - The ID of the product to add.
     * @param {number} [qty=1] - The quantity to add.
     * @returns {Promise<Object>} The JSON response from the server.
     */
    function cordageAddToCart(productId, qty) {
        qty = qty || 1;
        return fetch('/shop/cart/update_json', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({
                jsonrpc: '2.0', method: 'call', id: 1,
                params: {
                    product_id: parseInt(productId),
                    add_qty: qty,
                }
            })
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var qty_in_cart = data.result && data.result.cart_quantity;
            updateBadge(qty_in_cart);
            cordageToast('Added to cart ✓');
            renderCordageCart();
            openCordageCart();
            return data;
        });
    }
    
    /**
     * Changes the quantity of an item in the cart.
     * @param {string|number} lineId - The ID of the cart line.
     * @param {string|number} productId - The ID of the product.
     * @param {number} qty - The new quantity to set.
     * @returns {Promise<void>}
     */
    function changeQty(lineId, productId, qty) {
        return fetch('/shop/cart/update_json', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({
                jsonrpc: '2.0', method: 'call', id: 1,
                params: {
                    line_id: parseInt(lineId),
                    product_id: parseInt(productId),
                    set_qty: qty,
                }
            })
        })
        .then(r => r.json())
        .then(data => {
            if (data.result) {
                updateBadge(data.result.cart_quantity);
                renderCordageCart();
            }
        });
    }

    /**
     * Updates the cart badge with the given quantity.
     * @param {number} qty - The total quantity of items in the cart.
     */
    function updateBadge(qty) {
        var badge = document.querySelector('.my_cart_quantity');
        if (badge && qty != null) {
            badge.textContent = qty;
            badge.classList.remove('d-none');
            badge.animate(
                [{ transform: 'scale(1.6)' }, { transform: 'scale(1)' }],
                { duration: 300 }
            );
        }
    }

    /**
     * Displays a toast notification message.
     * @param {string} msg - The message to display in the toast.
     */
    function cordageToast(msg) {
        var el = document.getElementById('cordageToast');
        if (!el) return;
        el.textContent = msg;
        el.classList.add('show');
        clearTimeout(el._timer);
        el._timer = setTimeout(function () {
            el.classList.remove('show');
        }, 2400);
    }

    /**
     * Fetches cart data from the server and renders the custom cart UI.
     */
    function renderCordageCart() {
        fetch('/cordage/cart/data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: {} })
        })
        .then(r => r.json())
        .then(data => {
            if (!data.result) return;
            const res = data.result;
            const body = document.getElementById('cordageCartBody');
            if (res.cart.length === 0) {
                body.innerHTML = `<div class="cart__empty"><span>🪢</span>Your cart is empty.<br/>Add some rope to get started.</div>`;
            } else {
                body.innerHTML = res.cart.map(i => `
                <div class="cart-item">
                    <div class="cart-item__img" style="position:relative;overflow:hidden">
                        <img src="${i.imgUrl}" alt="${i.name}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:1"/>
                    </div>
                    <div>
                        <div class="cart-item__title">${i.name}</div>
                        <div class="cart-item__opt">${i.unit}</div>
                        <div class="cart-item__price">$${(i.price * i.qty).toFixed(2)}</div>
                        <div class="qty" style="display:flex;align-items:center;gap:10px;margin-top:5px;border:1px solid #ccc;padding:2px 5px;width:fit-content;border-radius:4px;">
                            <button style="border:none;background:none;cursor:pointer" data-dec="${i.line_id}" data-pid="${i.id}" data-qty="${i.qty}">−</button>
                            <span style="font-size:0.9rem">${i.qty}</span>
                            <button style="border:none;background:none;cursor:pointer" data-inc="${i.line_id}" data-pid="${i.id}" data-qty="${i.qty}">+</button>
                        </div>
                    </div>
                    <button class="cart-item__remove" data-remove="${i.line_id}" data-pid="${i.id}">✕</button>
                </div>`).join('');
            }
            
            document.getElementById('cordageCartSubtotal').textContent = '$' + res.subtotal.toFixed(2);
            document.getElementById('cordageCartTotal').textContent = '$' + res.total.toFixed(2);
        });
    }

    /**
     * Opens the custom cart drawer and overlay, then triggers a re-render.
     */
    function openCordageCart() {
        document.getElementById('cordageCustomCart')?.classList.add('open');
        const overlay = document.getElementById('cordageCartOverlay');
        if (overlay) overlay.style.display = 'block';
        renderCordageCart();
    }

    /**
     * Closes the custom cart drawer and overlay.
     */
    function closeCordageCart() {
        document.getElementById('cordageCustomCart')?.classList.remove('open');
        const overlay = document.getElementById('cordageCartOverlay');
        if (overlay) overlay.style.display = 'none';
    }

    /* Event Listeners */
    document.addEventListener('click', function (e) {
        var addBtn = e.target.closest('.cordage-add-cart');
        if (addBtn) {
            e.preventDefault();
            var pid = addBtn.dataset.productId;
            var qty = 1;
            
            // If button doesn't have dataset, look for a parent form
            if (!pid) {
                var form = addBtn.closest('form');
                if (form) {
                    var pidInput = form.querySelector('input[name="product_id"]');
                    var qtyInput = form.querySelector('input[name="add_qty"]');
                    if (pidInput) pid = pidInput.value;
                    if (qtyInput) qty = parseInt(qtyInput.value) || 1;
                }
            }
            if (!pid) return;
            addBtn.disabled = true;
            addBtn.textContent = 'Adding…';
            cordageAddToCart(pid, qty).finally(function () {
                addBtn.disabled = false;
                addBtn.textContent = 'Add to Cart';
            });
            return;
        }
        var cartLink = e.target.closest('a[href="/shop/cart"]');
        if (cartLink) {
            e.preventDefault();
            openCordageCart();
            return;
        }
        if (e.target.closest('#cordageCartClose') || e.target.closest('#cordageContinueBtn') || e.target.closest('#cordageCartOverlay')) {
            closeCordageCart();
            return;
        }
        var inc = e.target.closest('[data-inc]');
        if (inc) changeQty(inc.dataset.inc, inc.dataset.pid, parseInt(inc.dataset.qty) + 1);
        var dec = e.target.closest('[data-dec]');
        if (dec) changeQty(dec.dataset.dec, dec.dataset.pid, parseInt(dec.dataset.qty) - 1);
        var rem = e.target.closest('[data-remove]');
        if (rem) changeQty(rem.dataset.remove, rem.dataset.pid, 0);
    });

    window.cordageAddToCart = cordageAddToCart;
    window.cordageToast = cordageToast;
})();
