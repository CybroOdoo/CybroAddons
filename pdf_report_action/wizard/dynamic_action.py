# -*- coding: utf-8 -*-
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
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DynamicAction(models.TransientModel):
    """
        The class  DynamicAction provides print, share, open and download reports
        in various models .
        Methods:
            print_report(self):
                In this method print the screen of the form.Return a dict.
            download_report(self):
                In this method download the report of the form.Return a dict.
            open_report(self):
                In this methode open the print screen of the form.Return a dict.
            share_by_email(self):
                In this method share email report of the corresponding form.
                Return a dict.3.Some misspelled words are there in the doc
                string of the function. check it and correct it
    """
    _name = "dynamic.action"
    _description = "Dynamic Action"

    res_model = fields.Char('Related Document Model',
                            help='Model of the related document')
    res_id = fields.Integer('Related Document ID',
                            model_field='res_model',
                            help='ID of the related document')
    resource_ref = fields.Reference(string='Record',
                                    selection='_selection_target_model',
                                    inverse='_set_resource_ref',
                                    help='Reference to the record')

    @api.model
    def _selection_target_model(self):
        """ Reference field function"""
        domain = [('model', 'in', ['account.move', 'sale.order',
                                   'purchase.order', 'stock.picking'])]
        models_with_printing = self.env['ir.model'].sudo().search(domain)
        return [(model.model, model.name) for model in models_with_printing]

    def _set_resource_ref(self):
        """ Reference field function"""
        for participant in self:
            if participant.resource_ref:
                participant.res_id = participant.resource_ref.id
                participant.res_model = participant.resource_ref._name

    def _validate_record(self):
        """ Validate record model and type before executing report actions """
        self.ensure_one()
        if not self.res_model or not self.res_id:
            raise ValidationError(_("Please select a record!!!"))
        record = self.env[self.res_model].browse(self.res_id)
        if not record.exists():
            raise ValidationError(_("The selected record does not exist!!!"))
        if self.res_model == 'account.move' and record.move_type == 'entry':
            raise ValidationError(_("Only invoices could be printed."))
        return record

    def action_print_report(self):
        """ print button function"""
        self._validate_record()
        form_id = self.res_id
        model = self.res_model
        report_ref_map = {
            'sale.order': 'sale.action_report_saleorder',
            'purchase.order': 'purchase.action_report_purchase_order',
            'stock.picking': 'stock.action_report_picking',
            'account.move': 'account.account_invoices',
        }
        if model in report_ref_map:
            return self.env.ref(report_ref_map[model]).report_action([form_id])
        raise ValidationError(_("No record to print!!!"))

    def action_download_report(self):
        """
        Summary:
            In this method download the report of the form.Return a dict.
        Returns:
            type:dict , it contains the data for the download report.
        """
        self._validate_record()
        form_id = self.res_id
        model = self.res_model
        report_ref_map = {
            'sale.order': 'sale.action_report_saleorder',
            'purchase.order': 'purchase.action_report_purchase_order',
            'stock.picking': 'stock.action_report_picking',
            'account.move': 'account.account_invoices',
        }
        if model not in report_ref_map:
            raise ValidationError(_("Select a record to download!!!"))

        pdf_content, dummy = self.env['ir.actions.report']._render_qweb_pdf(
            report_ref_map[model], [form_id])
        record_name = self.env[model].browse(form_id).name or 'report'
        file_name = f"{record_name}.pdf"
        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'raw': pdf_content,
            'res_model': model,
            'res_id': form_id,
            'mimetype': 'application/pdf',
        })
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': f"/web/content/{attachment.id}?download=true",
        }

    def action_open_report(self):
        """
        Summary:
            In this method open the print screen of the form.Return a dict.
        Returns:
            type:dict , it contains the data for the open print report.
        """
        self._validate_record()
        form_id = self.res_id
        model = self.res_model
        report_ref_map = {
            'sale.order': 'sale.action_report_saleorder',
            'purchase.order': 'purchase.action_report_purchase_order',
            'stock.picking': 'stock.action_report_picking',
            'account.move': 'account.account_invoices',
        }
        if model not in report_ref_map:
            raise ValidationError(_("Select any record!!!"))

        report_action = self.env.ref(report_ref_map[model])
        report_name = report_action.report_name
        server_address = self.get_base_url()
        url = f"{server_address}/report/pdf/{report_name}/{form_id}"
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': url,
        }

    def action_share_email(self):
        """
        Summary:
            In this method share email report of the corresponding form.
            Return a dict.
        Returns:
            type:dict , it contains the data for the email template.
        """
        self._validate_record()
        form_id = self.res_id
        model = self.res_model
        model_name = self.resource_ref
        self.ensure_one()
        if model == 'sale.order':
            if model_name.state not in ('sale', 'done'):
                mail_template = self.env.ref('sale.email_template_edi_sale')
            else:
                mail_template = self.env.ref(
                    'sale.mail_template_sale_confirmation')
        elif model == 'purchase.order':
            if model_name.state not in ('purchase', 'done'):
                mail_template = self.env.ref(
                    'purchase.email_template_edi_purchase')
            else:
                mail_template = self.env.ref(
                    'purchase.email_template_edi_purchase_done')
        elif model == 'account.move':
            if model_name.move_type == 'out_refund':
                mail_template = self.env.ref(
                    'account.email_template_edi_credit_note')
            else:
                mail_template = self.env.ref(
                    'account.email_template_edi_invoice')
        else:
            raise ValidationError(_("select a record  or selected record does "
                                    "not have a share option!!!!!!"))
        ctx = {
            'default_model': model,
            'default_res_ids': [form_id],
            'default_use_template': bool(mail_template),
            'default_template_id': mail_template.id if mail_template else None,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_'
                                          'responsible_signature',
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
        }
        if mail_template:
            # If module has email template
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
                'context': ctx,
            }
        raise ValidationError(_("select a record  or selected record does not"
                                " have a share option!!!!!!!!!!!!"))
