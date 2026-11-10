## Module <backend_theme_infinito>

#### 17.07.2026
#### Version 18.0.1.0.0
#### ADD
Initial Commit for Infinito Backend Theme

#### 06.11.2026
#### Version 19.0.1.0.1
#### UPDT
- Updated JSON routes to type="jsonrpc" and Domain API for Odoo 19 compatibility.
- Replaced deprecated t-esc / t-raw / owl="1" and legacy odoo.define usage.
- Restricted theme save, reset and advanced-setting routes to Settings administrators.
- Dynamic CSS is now stored only in system parameters (no file write on disk).
- Fixed PWA manifest start URL and icon path.
#### FIX
- Fixed sidebar outside-click detection and full-screen app menu hiding the action area.
- Fixed typos in the description page and the theme editor help text.
#### ADD
- Added unit tests for controllers, PWA, icon hooks, recent apps, ir.http and settings.
#### REMOVE
- Removed the unused VisualEditor.js, dynamic_styles.css and duplicate image assets.

