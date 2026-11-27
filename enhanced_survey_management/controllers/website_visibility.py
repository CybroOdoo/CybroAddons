#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import http
from odoo.http import request


class WebsiteView(http.Controller):
    """Controller for public website survey visibility."""

    @http.route(
        '/public/survey',
        type='http',
        auth="public",
        website=True,
    )
    def public_user_access(self):
        """Render surveys published with website access mode."""
        survey = request.env['survey.survey'].sudo().search(
            [('access_mode', '=', 'website')],
        )
        values = {
            'survey_list': [{
                'title': rec.title,
                'attempts': rec.attempts_limit,
                'date': rec.create_date,
                'access_token': rec.access_token,
            } for rec in survey],
            'page_name': 'survey',
        }
        return request.render(
            "enhanced_survey_management.survey_visibility",
            values,
        )
