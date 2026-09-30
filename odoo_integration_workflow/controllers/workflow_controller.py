# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions @cybrosys(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class WorkflowController(http.Controller):

    @http.route('/api/workflows/autosave', type='json', auth='user')
    def autosave_workflow(self, **kw):
        """
        Extracts ID and Data correctly from the OWL Builder payload.
        """
        wrapper = kw.get('workflow_data', {})
        workflow_id = wrapper.get('id')
        workflow_content = wrapper.get('workflow', {})

        if not workflow_id:
            return {'status': 'ignored', 'message': 'Workflow not yet saved to database'}

        try:
            workflow = request.env['api.workflow'].sudo().browse(int(workflow_id))
            if workflow.exists():
                workflow.write({
                    'workflow_data': json.dumps(workflow_content)
                })
                return {'status': 'success'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

        return {'status': 'error', 'message': 'Workflow not found'}

