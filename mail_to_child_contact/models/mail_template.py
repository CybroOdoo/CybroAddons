# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Adarsh K (odoo@cybrosys.com)
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
###############################################################################
import itertools
from odoo import models, tools
from odoo.addons.mail.models.mail_template import MailTemplate


class MailTemplate(models.Model):
    """Inherit the class to send mail to all customer contacts."""
    _inherit = "mail.template"

    def _generate_template_recipients(self, res_ids, render_fields,
                                      find_or_create_partners=False,
                                      render_results=None):
        """ Render recipients of the template 'self', returning values for
        records given by 'res_ids'. Default values can be generated instead
        of the template values if requested by template (see 'use_default_to'
        field). Email fields ('email_cc', 'email_to') are transformed into
        partners if requested
        (finding or creating partners). 'partner_to' field is transformed into
        'partner_ids' field.
        Note: for performance reason, information from records are transferred
        to created partners no matter the company. For example, if we have a
        record of company A and one of B with the same email and no related
        partner, a partner will be created with company A or B but populated
        with information from the 2 records. So some info might be leaked
        from one company to the other through
        the partner.
        :param list res_ids: list of record IDs on which template is rendered;
        :param list render_fields: list of fields to render on template which
          are specific to recipients, e.g. email_cc, email_to, partner_to);
        :param boolean find_or_create_partners: transform emails into partners
          (calling ``find_or_create`` on partner model);
        :param dict render_results: res_ids-based dictionary of render values.
          For each res_id, a dict of values based on render_fields is given;
        :return: updated (or new) render_results. It holds a 'partner_ids' key
          holding partners given by ``_message_get_default_recipients`` and/or
          generated based on 'partner_to'. If ``find_or_create_partners`` is
          False emails are present, otherwise they are included as partners
          contained in ``partner_ids``.
        """
        self.ensure_one()
        if render_results is None:
            render_results = {}
        ModelSudo = self.env[self.model].with_prefetch(res_ids).sudo()
        # if using default recipients -> ``_message_get_default_recipients``
        # gives
        # values for email_to, email_cc and partner_ids
        if self.use_default_to and self.model:
            default_recipients = \
                ModelSudo.browse(res_ids)._message_get_default_recipients()
            for res_id, recipients in default_recipients.items():
                render_results.setdefault(res_id, {}).update(recipients)
        # render fields dynamically which generates recipients
        else:
            for field in set(render_fields) & {'email_cc', 'email_to',
                                               'partner_to'}:
                generated_field_values = self._render_field(field, res_ids)
                for res_id in res_ids:
                    render_results.setdefault(res_id, {})[field] = \
                        generated_field_values[res_id]
        # create partners from emails if asked to
        if find_or_create_partners:
            res_id_to_company = {}
            if self.model and 'company_id' in ModelSudo._fields:
                for read_record in ModelSudo.browse(res_ids).read(
                        ['company_id']):
                    company_id = read_record['company_id'][0] if read_record[
                        'company_id'] else False
                    res_id_to_company[read_record['id']] = company_id
            all_emails = []
            email_to_res_ids = {}
            email_to_company = {}
            for res_id in res_ids:
                record_values = render_results.setdefault(res_id, {})
                mails = tools.email_split(
                    record_values.pop('email_to', '')) + tools.email_split(
                    record_values.pop('email_cc', ''))
                all_emails += mails
                record_company = res_id_to_company.get(res_id)
                for mail in mails:
                    email_to_res_ids.setdefault(mail, []).append(res_id)
                    if record_company:
                        email_to_company[mail] = record_company
            if all_emails:
                customers_information = \
                    ModelSudo.browse(res_ids)._get_customer_information()
                partners = self.env['res.partner']._find_or_create_from_emails(
                    all_emails,
                    additional_values={
                        email: {
                            'company_id': email_to_company.get(email),
                            **customers_information.get(email, {}),
                        }
                        for email in itertools.chain(all_emails, [False])
                    })
                for original_email, partner in zip(all_emails, partners):
                    if not partner:
                        continue
                    for res_id in email_to_res_ids[original_email]:
                        render_results[res_id].setdefault(
                            'partner_ids', []).append(partner.id)
        # update 'partner_to' rendered value to 'partner_ids'
        all_partner_to = {
            pid
            for record_values in render_results.values()
            for pid in self._parse_partner_to(record_values.get(
                'partner_to', ''))
        }
        existing_pids = set()
        if all_partner_to:
            existing_pids = set(
                self.env['res.partner'].sudo().browse(
                    list(all_partner_to)).exists().ids)
        for res_id, record_values in render_results.items():
            partner_to = record_values.pop('partner_to', '')
            if partner_to:
                tpl_partner_ids = set(
                    self._parse_partner_to(partner_to)) & existing_pids
                record_values.setdefault(
                    'partner_ids', []).extend(tpl_partner_ids)
        res_id = res_ids[0]
        partner_id = render_results[res_id]['partner_ids'][0]
        partner_ids = self.env['res.partner'].sudo().search(
            [('commercial_partner_id', '=', partner_id)])
        for rec in partner_ids:
            render_results[res_id].setdefault('partner_ids', []).append(rec.id)
        return render_results

    MailTemplate._generate_template_recipients = _generate_template_recipients
