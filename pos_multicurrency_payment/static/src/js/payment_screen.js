import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);

        const config = this.pos?.config;
        if (!config?.pos_multi_currency_enabled) return;

        this._orm = useService("orm");
        this._isApplying = false;
        this._mcMeta = new WeakMap();

        onMounted(() => this._initPanel());
        onWillUnmount(() => {
            this._removeMcOverlay();
            if (this._mcDiv) { this._mcDiv.remove(); this._mcDiv = null; }
        });
    },

    _getCurrentOrder() {
        return this.currentOrder ?? this.pos.selectedOrder ?? this.pos.getOrder?.() ?? null;
    },

    _getOrderTotal(order) {
        if (!order) return 0;
        return order.totalDue ?? order.priceIncl ?? 0;
    },

    async _initPanel() {
        let currencies = [];
        try {
            const configId = this.pos.config.id;
            const configData = await this._orm.read("pos.config", [configId], ["pos_allowed_currency_ids"]);
            const currencyIds = configData?.[0]?.pos_allowed_currency_ids || [];
            if (currencyIds.length) {
                currencies = await this._orm.read("res.currency", currencyIds,
                    ["id", "name", "symbol", "rate", "decimal_places", "active"]);
                currencies = currencies.filter(c => c.active !== false);
            }
        } catch (e) { console.error("[MC] Failed to fetch currencies:", e); }
        if (!currencies.length) return;
        this._tryMountPanel(currencies, 0);
    },

    _tryMountPanel(currencies, attempt) {
        if (attempt > 15) { console.error("[MC] Mount failed."); return; }
        setTimeout(() => {
            if (this._mcDiv && document.contains(this._mcDiv)) return;
            const selectors = [
                ".payment-screen .left-content",
                ".payment-screen .payment-left",
                ".payment-screen .left",
                ".payment-screen > div > div:first-child",
                ".payment-screen > div:first-child",
                ".payment-screen",
            ];
            let container = null;
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el) { container = el; break; }
            }
            if (!container) { this._tryMountPanel(currencies, attempt + 1); return; }
            this._renderPanel(container, currencies);
        }, 300 * (attempt + 1));
    },

    _removeMcOverlay() {
        const orig = document.getElementById("mc-original-total");
        if (orig) orig.style.visibility = "";
        document.getElementById("mc-big-overlay")?.remove();
        document.querySelectorAll(".mc-line-label").forEach(el => el.remove());
    },

    _stampBigTotal(symbol, amountForeign, sessionAmount, sessionName) {
        setTimeout(() => {
            this._removeMcOverlay();

            let bigEl = null;
            const candidates = document.querySelectorAll(".payment-screen *");
            const amtStr = sessionAmount.toFixed(2);

            for (const el of candidates) {
                const hasAmount = el.textContent.replace(/\s/g, "").includes(
                    amtStr.replace(".", "").replace(/^0+/, "")
                );
                const isLarge = parseFloat(window.getComputedStyle(el).fontSize) >= 36;
                const isLeaf = el.children.length === 0 || [...el.children].every(
                    c => ["SPAN", "SUP", "SUB"].includes(c.tagName)
                );
                if (hasAmount && isLarge && isLeaf) { bigEl = el; break; }
            }

            if (!bigEl) {
                const knownSels = [
                    ".payment-screen .payment-total",
                    ".payment-screen .total",
                    ".payment-screen .amount-total",
                    ".payment-screen .order-total",
                ];
                for (const sel of knownSels) {
                    bigEl = document.querySelector(sel);
                    if (bigEl) break;
                }
            }

            if (!bigEl) { console.warn("[MC] Could not locate big total element."); return; }

            bigEl.id = "mc-original-total";
            const rect = bigEl.getBoundingClientRect();
            const scrollTop = window.scrollY || document.documentElement.scrollTop;
            bigEl.style.visibility = "hidden";

            const overlay = document.createElement("div");
            overlay.id = "mc-big-overlay";
            overlay.style.cssText = [
                `position:absolute`,
                `top:${rect.top + scrollTop}px`,
                `left:${rect.left}px`,
                `width:${rect.width}px`,
                `min-height:${rect.height}px`,
                `z-index:999`,
                `display:flex`,
                `flex-direction:column`,
                `align-items:center`,
                `justify-content:center`,
                `pointer-events:none`,
            ].join(";");

            const currLabel = document.createElement("div");
            currLabel.style.cssText = [
                "font-size:16px",
                "font-weight:600",
                "color:#6c757d",
                "letter-spacing:2px",
                "text-transform:uppercase",
                "margin-bottom:0px",
                "line-height:1",
            ].join(";");
            currLabel.textContent = symbol;

            const amountEl = document.createElement("div");
            const computedFs = parseFloat(window.getComputedStyle(bigEl).fontSize) || 72;
            amountEl.style.cssText = [
                `font-size:${computedFs}px`,
                "font-weight:700",
                "color:#101010",
                "line-height:1.05",
                "letter-spacing:-2px",
                "font-family:inherit",
            ].join(";");
            amountEl.textContent = amountForeign.toFixed(2);

            const subLabel = document.createElement("div");
            subLabel.style.cssText = [
                "font-size:13px",
                "color:#aaa",
                "margin-top:4px",
                "letter-spacing:0.5px",
            ].join(";");
            subLabel.textContent = `${sessionName} ${sessionAmount.toFixed(2)}`;

            overlay.appendChild(currLabel);
            overlay.appendChild(amountEl);
            overlay.appendChild(subLabel);
            document.body.appendChild(overlay);
        }, 150);
    },

    _stampPaymentLineLabel(symbol, amountForeign, sessionAmount, sessionName) {
        setTimeout(() => {
            document.querySelectorAll(".mc-line-label").forEach(el => el.remove());

            const rowSelectors = [
                ".paymentlines .paymentline",
                ".payment-lines .paymentline",
                ".payment-lines .payment-line",
                ".payment-screen-payment-lines .paymentline",
                "[class*='paymentline']",
            ];
            let rows = [];
            for (const sel of rowSelectors) {
                rows = [...document.querySelectorAll(sel)];
                if (rows.length) break;
            }
            if (!rows.length) return;

            const lastRow = rows[rows.length - 1];
            lastRow.style.position = "relative";

            const existingAmt = lastRow.querySelector(".amount, .payment-amount, [class*='amount']");
            if (existingAmt) {
                existingAmt.style.color = "#aaa";
                existingAmt.style.fontSize = "13px";
            }

            const chip = document.createElement("div");
            chip.className = "mc-line-label";
            chip.style.cssText = "display:flex;flex-direction:column;align-items:flex-end;line-height:1.2;";

            const bigAmt = document.createElement("span");
            bigAmt.style.cssText = "font-size:18px;font-weight:700;color:#212529;";
            bigAmt.textContent = `${symbol} ${amountForeign.toFixed(2)}`;

            const smallAmt = document.createElement("span");
            smallAmt.style.cssText = "font-size:11px;color:#aaa;";
            smallAmt.textContent = `${sessionName} ${sessionAmount.toFixed(2)}`;

            chip.appendChild(bigAmt);
            chip.appendChild(smallAmt);

            const closeBtn = lastRow.querySelector("button, .delete-button, [class*='delete']");
            if (closeBtn) lastRow.insertBefore(chip, closeBtn);
            else lastRow.appendChild(chip);
        }, 200);
    },

    _renderPanel(container, currencies) {
        const sessionCurrency = this.pos.currency;
        const sessionName = sessionCurrency?.name || "USD";

        const options = currencies.map(c =>
            `<option value="${c.id}" data-rate="${c.rate}" data-symbol="${c.symbol}" data-name="${c.name}">
                ${c.name} (${c.symbol})
            </option>`
        ).join("");

        const div = document.createElement("div");
        div.id = "pos-mc-panel";
        div.className = "pos-mc-panel";
        div.innerHTML = `
            <div class="pos-mc-header">
                <span class="pos-mc-header-icon">💱</span>
                <span class="pos-mc-header-title">Currency Converter</span>
            </div>
            <div class="pos-mc-body">
                <div class="pos-mc-field">
                    <label class="pos-mc-label">Select Currency</label>
                    <div class="pos-mc-select-wrap">
                        <select class="pos-mc-select">
                            <option value="">— choose currency —</option>
                            ${options}
                        </select>
                        <span class="pos-mc-select-arrow">▼</span>
                    </div>
                </div>

                <div class="pos-mc-rate-card" id="mc-rate-card">
                    <div class="pos-mc-rate-row">
                        <span class="pos-mc-rate-label">Exchange Rate</span>
                        <span class="pos-mc-rate-value" id="mc-rate-val">—</span>
                    </div>
                    <div class="pos-mc-divider"></div>
                    <div class="pos-mc-rate-row">
                        <span class="pos-mc-rate-label">Amount Due</span>
                        <span class="pos-mc-rate-value pos-mc-total-value" id="mc-total-val">—</span>
                    </div>
                </div>

                <button class="pos-mc-btn" id="mc-apply-btn">
                    <span class="pos-mc-btn-icon">✓</span>
                    <span class="pos-mc-btn-text">Apply Payment</span>
                </button>

                <div id="mc-status" class="pos-mc-status" style="display:none;"></div>
            </div>
        `;

        const select = div.querySelector(".pos-mc-select");
        const rateVal = div.querySelector("#mc-rate-val");
        const totalVal = div.querySelector("#mc-total-val");
        const btn = div.querySelector("#mc-apply-btn");
        const statusEl = div.querySelector("#mc-status");
        const rateCard = div.querySelector("#mc-rate-card");

        const getConvRate = (opt) => {
            const sessionRate = parseFloat(sessionCurrency?.rate) || 1.0;
            const targetRate = parseFloat(opt?.dataset?.rate) || 1.0;
            return targetRate / sessionRate;
        };

        const showStatus = (msg, isError = false) => {
            statusEl.textContent = msg;
            statusEl.style.display = "flex";
            statusEl.className = `pos-mc-status ${isError ? "pos-mc-status--error" : "pos-mc-status--success"}`;
            clearTimeout(this._mcStatusTimer);
            this._mcStatusTimer = setTimeout(() => {
                statusEl.style.display = "none";
                statusEl.className = "pos-mc-status";
            }, 4000);
        };

        const updateDisplay = () => {
            const opt = select.options[select.selectedIndex];
            if (!opt?.value) {
                rateVal.textContent = "—";
                totalVal.textContent = "—";
                rateCard.classList.remove("pos-mc-rate-card--active");
                return;
            }
            const order = this._getCurrentOrder();
            const total = this._getOrderTotal(order);
            const convRate = getConvRate(opt);
            const converted = total * convRate;
            rateVal.textContent = `1 ${sessionName} = ${convRate.toFixed(4)} ${opt.dataset.symbol}`;
            totalVal.textContent = `${opt.dataset.symbol} ${converted.toFixed(2)}`;
            rateCard.classList.add("pos-mc-rate-card--active");
        };

        const resolvePaymentLines = (rawLines) => {
            if (!rawLines) return [];
            if (Array.isArray(rawLines)) return [...rawLines];
            if (rawLines[Symbol.iterator]) return [...rawLines];
            if (typeof rawLines === "object")
                return rawLines.records ?? rawLines.data ?? Object.values(rawLines);
            return [];
        };

        btn.addEventListener("click", () => {
            if (this._isApplying) return;
            this._isApplying = true;
            btn.disabled = true;
            btn.classList.add("pos-mc-btn--loading");
            const btnText = btn.querySelector(".pos-mc-btn-text");
            if (btnText) btnText.textContent = "Applying…";

            try {
                const opt = select.options[select.selectedIndex];
                if (!opt?.value) { alert("Please select a currency."); return; }

                const order = this._getCurrentOrder();
                if (!order) { alert("No active order."); return; }

                const fullTotal = this._getOrderTotal(order);
                const convRate = getConvRate(opt);
                const amountForeign = fullTotal * convRate;

                // 1. Clear existing lines
                for (const line of resolvePaymentLines(order.payment_ids)) {
                    try { order.removePaymentline(line); } catch (e) { /**/ }
                }

                // 2. Find payment method
                let pm = null;
                const fromConfig = this.payment_methods_from_config;
                if (Array.isArray(fromConfig) && fromConfig.length) {
                    pm = fromConfig.find(m => m.type === "cash")
                        || fromConfig.find(m => m.is_cash_count)
                        || fromConfig[0];
                }
                if (!pm) {
                    const allPMs = this.pos.models?.["pos.payment.method"]?.getAll?.() ?? [];
                    pm = allPMs.find(m => m.type === "cash") ?? allPMs[0];
                }
                if (!pm) { alert("No payment method found."); return; }

                // 3. Add line
                order.addPaymentline(pm);
                let line = order.getSelectedPaymentline?.();
                if (!line) {
                    const arr = resolvePaymentLines(order.payment_ids);
                    line = arr[arr.length - 1];
                }
                if (!line) { showStatus("Error: could not create payment line.", true); return; }

                // 4. Set amounts
                line.setAmount(fullTotal);
                try {
                    line.update({ amount_currency: amountForeign });
                } catch (e) {
                    console.warn("[MC] amount_currency not in schema:", e.message);
                }

                // 5. Store metadata
                this._mcMeta.set(line, {
                    currency_id: parseInt(opt.value),
                    currency_name: opt.dataset.name,
                    currency_symbol: opt.dataset.symbol,
                    amount_foreign: amountForeign,
                    session_amount: fullTotal,
                    session_name: sessionName,
                });

                // 6. Update UI
                this._stampBigTotal(opt.dataset.symbol, amountForeign, fullTotal, sessionName);
                this._stampPaymentLineLabel(opt.dataset.symbol, amountForeign, fullTotal, sessionName);

                // 7. Success state
                btn.classList.remove("pos-mc-btn--loading");
                btn.classList.add("pos-mc-btn--success");
                const icon = btn.querySelector(".pos-mc-btn-icon");
                if (icon) icon.textContent = "✓";
                if (btnText) btnText.textContent = "Payment Applied!";
                showStatus(`✓ ${opt.dataset.symbol} ${amountForeign.toFixed(2)} applied successfully`);
                updateDisplay();

                setTimeout(() => {
                    btn.classList.remove("pos-mc-btn--success");
                    if (btnText) btnText.textContent = "Apply Payment";
                    if (icon) icon.textContent = "✓";
                }, 3000);

            } catch (e) {
                console.error("[MC] Error:", e);
                showStatus("Error: " + e.message, true);
                btn.classList.remove("pos-mc-btn--loading");
                if (btnText) btnText.textContent = "Apply Payment";
            } finally {
                setTimeout(() => { this._isApplying = false; btn.disabled = false; }, 400);
            }
        });

        select.addEventListener("change", () => {
            this._removeMcOverlay();
            updateDisplay();
            // Reset button if currency changed after applying
            btn.classList.remove("pos-mc-btn--success");
            const btnText = btn.querySelector(".pos-mc-btn-text");
            if (btnText) btnText.textContent = "Apply Payment";
        });

        container.appendChild(div);
        this._mcDiv = div;

        if (select.options.length > 1) { select.selectedIndex = 1; updateDisplay(); }
    },
});