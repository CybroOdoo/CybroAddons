# Odoo 19 POS Partial Payment - Technical Documentation & PR Guide

## 1. Overview & Problem Statement

In Odoo Point of Sale, partial payments allow customers to pay for their purchases in multiple installments or invoice the remaining balance.

### Previous Limitation
In previous module versions (v16/v18):
- When an order was partially paid and invoiced, paying the remaining balance via backend Accounting (**Customer Invoices → Register Payment**) did **not** sync back to the POS order.
- No `pos.payment` entry was created on the POS order for the remaining payment.
- The POS order's `amount_paid` was not updated accurately based on invoice payments, and order state transition to `paid` relied on finding an open POS session for the logged-in user.

### Solution Introduced in Odoo 19
This upgrade adds a complete synchronization bridge between backend Accounting payments and POS orders:
1. Detects when an invoice originates from a partially paid POS order.
2. Prompts the accountant for a **POS Payment Method** on the **Register Payment** wizard.
3. Automatically creates a `pos.payment` audit line on the target POS order.
4. Increments `amount_paid` and sets `state = 'paid'` once the order is fully settled.

---

## 2. Technical Architecture & File Changes

### Models (`models/`)

1. **`models/account_move.py`** (`[NEW]`)
   - **`is_pos_order`** (`Boolean`, computed): Checks if the invoice (`account.move`) is linked to a partially paid POS order (`state == 'invoiced'` and `is_partial_payment == True`).
   - **`action_register_payment()`** (overridden): Injects `'is_pos_order': True` into context when launching the payment wizard from an invoice.

2. **`models/account_payment_register.py`** (`[UPDATE]`)
   - **`is_pos_order`** (`Boolean`, computed): Evaluates invoice move IDs (`line_ids.move_id` or context `active_ids`).
   - **`pos_payment_method_id`** (`Many2one` to `pos.payment.method`): Field to select the POS payment method for the backend payment.
   - **`action_create_payments()`** (overridden):
     - Locates target `pos.order`.
     - Creates `pos.payment` record (`pos_order_id`, `amount`, `payment_method_id`).
     - Updates `amount_paid` on the POS order.
     - Sets POS order `state = 'paid'` and `is_partial_payment = False` when `amount_paid >= amount_total`.

3. **`models/pos_order.py`**
   - Computes `due_amount` and handles POS partial order search queries (`search_partial_order_ids`).

### Views (`views/`)

1. **`views/account_payment_register_views.xml`** (`[NEW]`)
   - Inherits `account.view_account_payment_register_form`.
   - Adds `pos_payment_method_id` field visible when `is_pos_order` is True, using modern Odoo 19 syntax (`invisible="not is_pos_order"` and `required="is_pos_order"`).

### Frontend Assets (`static/src/`)

1. **`js/payment_screen.js`**: Patch for POS `PaymentScreen` to validate partial payments, ensure partner & invoice are set, and bypass full payment checks for partial orders.
2. **`js/ticket_screen.js`**: Patch for `TicketScreen` adding a **Partial** order state filter and fetching partial orders server-side.
3. **`js/models.js`**: Serialization patch for `PosOrder` model to transfer `is_partial_payment` flag to server ORM calls.

---

## 3. GitHub Pull Request Draft Template

Below is a ready-to-use template for submitting your PR to `CybroAddons`:

```markdown
### [19.0][UPG/IMP] pos_partial_payment_odoo: Upgrade to Odoo 19 & add Accounting invoice payment sync

#### Description
This PR upgrades `pos_partial_payment_odoo` to **Odoo 19** and adds complete backend accounting payment synchronization for partially paid POS orders.

#### Key Changes

1. **Odoo 19 Compatibility**:
   - Upgraded Python models to Odoo 19 ORM standards.
   - Converted XML views from deprecated `attrs="{...}"` syntax to Odoo 19 `invisible` / `required` expressions.
   - Refactored frontend OWL JavaScript patches (`PaymentScreen`, `TicketScreen`, `PosOrder`) using `@web/core/utils/patch`.

2. **Accounting Invoice Payment Sync**:
   - Extended `account.move` with `is_pos_order` compute field and contextual payment action overrides.
   - Extended `account.payment.register` wizard to display `pos_payment_method_id` when registering payments on POS invoices.
   - Automatically creates `pos.payment` records on the POS order, updates `amount_paid`, and transitions order state to `paid` when the invoice balance is settled.

#### Testing & Verification
- Tested POS order flow with partial payment & invoice generation.
- Verified backend invoice payment registration from **Accounting -> Invoices -> Register Payment**.
- Verified `pos.payment` entries, `amount_paid`, and state update on POS orders.
- Verified python compilation (`py_compile`) and asset bundling.
```
