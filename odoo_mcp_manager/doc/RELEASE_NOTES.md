## Module <odoo_mcp_manager>

#### Version 20.0.1.0.0
#### MIGRATION
- Migrated module to Odoo master (v20.0/19.5a1).
- Updated security access rules to master format (`security/ir.access.csv` with `operation` column).
- Migrated `ir.config_parameter` calls to typed accessors (`get_str`, `set_str`).
- Migrated ORM constraints from `_sql_constraints` to `models.Constraint`.
- Migrated deprecated `name_get()` to `@api.depends(...)` and `_compute_display_name`.
- Updated Owl frontend components to Owl 3 (`proxy`, `standardActionServiceProps`, `t-out`, `this.` scoping, `t-ref="this.textareaRef"`).
- Updated wizards to use `self.env.context` instead of `self._context`.
- Updated unit test suite to test new ORM behaviors and typed parameters.

#### 04.06.2026
#### Version 19.0.1.0.0
#### ADD
- Initial commit for Odoo MCP Gateway
