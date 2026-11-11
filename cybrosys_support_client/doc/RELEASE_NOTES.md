## Module <cybrosys_support_client>

#### 13.06.2024
#### Version 19.0.1.0.0
#### ADD
- Initial commit

#### 12.08.2026
#### Version 19.0.1.0.1
#### UPDT
- Updated CSS to ensure consistent UI styling and flexibility across both light and dark modes.
#### 11.11.2026
#### Version 19.0.1.1.0
#### UPDT
- Requests to the support server now carry the module's API key (required by the server from cybrosys_support_server 19.0.2.1.0).
- Attachments are limited to images, PDF and Word documents, at most 5 files of 3 MB each, checked before sending.
- Clear messages for rejected requests (rate limit, file type or size, outdated module).
