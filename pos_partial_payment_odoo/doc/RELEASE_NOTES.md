## Module `pos_partial_payment_odoo`

#### 23.07.2026
#### Version 19.0.1.0.0
### ADD / UPG / FIX

- **Odoo 19 Migration**: Upgraded module models, views, and frontend OWL JS patches for full Odoo 19 compatibility.
- **Accounting Payment Synchronization**: Extended `account.move` and `account.payment.register` to support registering partial payment on invoiced POS orders via backend Accounting.
- **POS Payment Method Selection**: Added POS payment method selection on payment wizard with automatic creation of `pos.payment` records, updating `amount_paid`, and transitioning POS order state to `paid`.
- **View Syntax Modernization**: Replaced deprecated `attrs="{...}"` in XML forms with Odoo 19 `invisible` and `required` attributes.

#### 23.04.2026
#### Version 18.0.1.0.0
### ADD

- Initial Commit for POS Partial Payment in Odoo 18.
