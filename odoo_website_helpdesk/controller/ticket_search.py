from odoo import http
from odoo.http import request


class TicketSearch(http.Controller):
    @http.route(['/ticketsearch'], type='json', auth="public", website=True)
    def ticket_search(self, **kwargs):
        search_value = kwargs.get("search_value")
        tickets = request.env["help.ticket"].search(
            ['|', ('name', 'ilike', search_value),
             ('subject', 'ilike', search_value)])

        values = {
            'tickets': tickets,
        }
        response = http.Response(template='odoo_website_helpdesk.ticket_table',
                                 qcontext=values)
        return response.render()
