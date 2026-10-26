## Module <wm_collection>

#### 19.08.2026
#### Version 19.0.1.0.0
##### ADD
- Initial commit for Waste Management Collection & Inventory.
- Added collection orders, service zones, route optimization, map view, vehicle checklists, missed collection workflows, and waste batch inventory.

#### 23.09.2026
#### Version 19.0.1.0.1
##### UPDT
- Updated the index page

#### 12.10.2026
#### Version 19.0.1.0.2
##### UPDT
- Added weighbridge gate entry tracking for trucks and waste weights.
- Added container tracking with barcodes and RFID tags.
- Added audit logs for collection order status changes.
- Automatically created waste batches when a route is completed.
- Automatically created driver shifts when a route is dispatched.
- Tightened record rules: drivers only reach their own status logs, missed collections and signatures; read access is limited to the Waste Management roles.
- Added multi-company rules for batch lines and gate entry lines.
- Moved the delete guards to ondelete methods and fixed the inheritable defaults of waste batches.
