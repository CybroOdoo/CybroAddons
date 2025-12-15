## Module <pos_restrict_product_stock>

#### 16.09.2023
#### Version 16.0.1.0.0
#### ADD
Initial Commit for Display Stock in POS | Restrict Out-of-Stock Products in POS

#### 12.06.2024
#### Version 16.0.1.0.1
#### ADD
Code updated that quantity would be shown based on the warehouse in the operation type. Considered the case of 
multiple warehouse

#### 18.07.2024
#### Version 16.0.2.1.1
#### ADD
- Code updated. that quantity and forcast quantity would be updated in real time when a pos order was confirmed when 
Also Changed the quantity visible for service product

#### 11.11.2024
#### Version 16.0.2.2.2
#### Update
- Added a new feature that restricts stock availability when clicking the payment button. 
This will help prevent the ordering of out-of-stock products, whether entered via barcode or through any other method.

#### 25.06.2025
#### Version 16.0.2.2.2
#### Update
- Fixed the bug and updated the out-of-stock condition. If the product quantity is out of stock, a popup will be displayed.

#### 06.11.2025
#### Version 16.0.2.2.3
#### Update
- Service products and products measured with “To Weigh in Scale” enabled are now excluded from 
Restrict Product Out of Stock in POS.