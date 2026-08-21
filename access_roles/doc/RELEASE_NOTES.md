## Module <access_roles>

#### 21.07.2025
#### Version 18.0.1.0.0
##### ADD
- Initial commit for Access Roles.

#### 02.07.2026
#### Version 18.0.1.0.1
##### BUG_FIX
- Fixed the double modal issue and removed DeprecationWarning from the module. 

#### 16.07.2026
#### Version 18.0.1.0.2
##### BUG_FIX
- Moved database initialization to post_init_hook to resolve Odoo.sh startup performance and serialization issues.

#### 27.07.2026
#### Version 18.0.1.0.3
##### BUG_FIX
- Fixed the filter registry startup issue by adding exception handling and savepoints to prevent database errors during server initialization.


