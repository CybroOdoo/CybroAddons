# -*- coding: utf-8 -*-

from odoo.addons.website_mass_mailing.controllers.main import MassMailController
from odoo.http import route, request


class MassMailController(MassMailController):
    @route('/website_mass_mailing/subscribe', type='json', website=True, auth="public")
    def subscribe(self, list_id, email, **post):
        """
        Overrided function which treats the inputs when clicks on subscribe button.
        :param list_id:
        :param email:
        :param post: Will contain the Name entered on Input box.
        :return:
        """
        Contacts = request.env['mail.mass_mailing.contact'].sudo()
        name, email = Contacts.get_name_email(email)

        contact_ids = Contacts.search([
            ('list_id', '=', int(list_id)),
            ('email', '=', email),
        ], limit=1)
        if not contact_ids:
            # inline add_to_list as we've already called half of it
            Contacts.create({'name': post.get('name') or name, 'email': email, 'list_id': int(list_id)})
        elif contact_ids.opt_out:
            contact_ids.opt_out = False
        # add email to session
        request.session['mass_mailing_email'] = email
        return True
