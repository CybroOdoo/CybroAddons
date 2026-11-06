# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: FATHIMA SHALFA P (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import http
from odoo.http import request


class VibeDownloadController(http.Controller):
    """HTTP endpoints for downloading generated module ZIPs and
    exporting conversation history as JSON.
    """

    @http.route(
        "/vibe/module/<int:module_id>/download",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def download(self, module_id, **kwargs):
        """Stream the generated module ZIP to the browser."""
        # 1. Existence check first — browse() never raises on a missing ID.
        module = request.env["vibe.generated.module"].browse(module_id)
        if not module.exists():
            raise request.not_found()

        # 2. Explicit access checks at the controller boundary.
        #    Record rules protect ORM access, but we re-verify before streaming bytes.
        module.check_access("read")

        from ..services.module_packager import build_zip
        zip_bytes = build_zip(module)

        # Increment counter via sudo — the access checks above are already done.
        module.sudo().write({"download_count": module.download_count + 1})

        filename = "%s.zip" % module.technical_name
        headers = [
            ("Content-Type", "application/zip"),
            ("Content-Disposition", "attachment; filename=\"%s\"" % filename),
            ("Content-Length", str(len(zip_bytes))),
        ]
        return request.make_response(zip_bytes, headers=headers)

    @http.route(
        "/vibe/conversation/<int:conversation_id>/export",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def export_conversation(self, conversation_id, **kwargs):
        """Download a conversation as a self-contained JSON file.

        Includes the full message history, every generated module with
        all file contents inlined, and token usage. Excludes API keys,
        user IDs, and other instance-specific data — the export is
        designed to be shareable.
        """
        conv = request.env["vibe.conversation"].browse(conversation_id)
        if not conv.exists():
            raise request.not_found()

        # Same access-check pattern as the module download
        conv.check_access("read")

        from ..services.conversation_exporter import build_export
        filename, json_bytes = build_export(conv)

        headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Disposition", 'attachment; filename="%s"' % filename),
            ("Content-Length", str(len(json_bytes))),
        ]
        return request.make_response(json_bytes, headers=headers)
