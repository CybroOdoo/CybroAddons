## Module <pos_kitchen_screen_odoo>

#### 23.05.2025
#### Version 18.0.1.0.0
#### ADD
- Initial commit for Pos Kitchen Screen

#### 29.05.2025
#### Version 18.0.1.1.0
#### BUG FIX
- Fixed issue where orders were not displaying on the kitchen screen.
- Fixed kitchen screen not updating according to POS order changes.
- Fixed completed orders incorrectly reverting to draft or cooking stage in kitchen screen after payment completion.

#### 14.06.2025
#### Version 18.0.1.1.1
#### BUG FIX
- Fixed issue where completed orders were still shown after the session was closed.


#### 15.07.2025
#### Version 18.0.1.1.2
#### BUG FIX
- Fixed issue where order reference in order list become mistmatch/wrong, get order ref from other POS.

#### 25.07.2025
#### Version 18.0.1.1.3
#### BUG FIX
- Fixed issue where latest orders disappearing from kitchen screen when plan button is clicked from POS.
- Fixed issue where orders in kitchen screen required manual refresh.
- Fixed issue when adding items to the order and quantity defaults to one. 

#### 07.08.2025
#### Version 18.0.1.1.4
#### BUG FIX
-Fixed the issue where a completed kitchen order reverted to 'Cooking' status after the payment was processed.

#### 03.09.2025
#### Version 18.0.1.2.0
#### BUG FIX
-Fixed the issue where, after completing an order and selecting the same floor again, the previously submitted order was duplicated in the POS order line.