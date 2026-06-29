## Module <laundry_management>

#### 26.01.2026
#### Version 19.0.1.0.0
#### ADD

- Initial commit for Laundry Management

#### 22.06.2026
#### Version 19.0.1.0.1
#### UPDATE

- Added comprehensive test suites for core models (`laundry.order`, `washing.type`, `washing.washing`, `washing.work`, `sale.advance.payment.inv`).
- Fixed Odoo 19 compatibility issues related to `res.groups` and `partner` NOT NULL constraints in test setup.
- Resolved 'Missing Record' issue when creating invoices from laundry orders by explicitly passing `active_id`, `active_ids`, and `active_model` context correctly for `sale.order`.
