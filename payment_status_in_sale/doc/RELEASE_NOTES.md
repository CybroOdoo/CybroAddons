## Module <payment_status_in_sale>

#### 16.03.2024
#### Version 16.0.1.0.0
##### ADD
- Initial commit for Sale Order Payment Status.

#### 04.02.2026
#### Version 16.0.1.0.1
##### BUG_FIX
- Issue resolved where Amount Due was incorrectly displayed as a negative value after the credit note had been fully settled.

#### 19.02.2026
#### Version 16.0.1.0.2
##### BUG_FIX
- Resolved the module issue where the amount due was incorrectly displayed for credit notes by mapping it to the amount_residual field in account.move.

#### 04.06.2026
#### Version 16.0.1.0.3
##### BUG_FIX
- Resolved the module issue where the payment status were not visible in form view.