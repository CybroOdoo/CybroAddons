## Module <wm_compliance>

#### 19.08.2026
#### Version 19.0.1.0.0
##### ADD
- Initial commit for Waste Management Compliance.
- Added waste stream manifests, chain of custody logs, SHA-256 digital certificates, permit document vault, environmental targets, compliance dashboard, and report builder wizard.

#### 23.09.2026
#### Version 19.0.1.0.1
##### UPDT
- Updated the index page

#### 12.10.2026
#### Version 19.0.1.0.2
##### UPDT
- Added safety incident reporting with OSHA tracking and photos.
- Added regional compliance rules for waste codes and document retention.
- Added status checks to prevent editing processed waste manifests.
- Declared the `fleet` and `uom` dependencies and hardened vault attachment cleanup, custody logging and rule precedence.
- Moved the delete guards to ondelete methods.
- Removed the duplicate disposal facility rule and access rows.
