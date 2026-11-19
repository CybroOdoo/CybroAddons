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
from odoo import http
from odoo.http import request


class ViewPortal(http.Controller):
    """Class holding portal view methods"""

    @http.route('/my/vaccinations', type='http', auth="public", website=True)
    def portal_my_vaccine(self, **kw):
        """Function for rendering vaccination details of portal user"""
        partner_id = request.env.user.partner_id.id
        domain = ['|', ('patient_id', '=', partner_id), ('patient_id.user_ids', 'in', [request.uid])]
        vaccination_list = []
        for rec in request.env['hospital.vaccination'].sudo().search(domain):
            attachment = request.env['ir.attachment'].sudo().search([
                ('res_id', '=', rec.id),
                ('res_model', '=', 'hospital.vaccination')
            ], limit=1)
            attachment_id = attachment.id if attachment else False
            access_token = ''
            if attachment:
                if not attachment.access_token:
                    attachment.generate_access_token()
                access_token = attachment.access_token or ''
            data = {
                'id': rec.id,
                'name': rec.name,
                'vaccine_date': rec.vaccine_date,
                'dose': rec.dose,
                'vaccine_product_id': rec.vaccine_product_id.name,
                'vaccine_price': rec.vaccine_price,
                'attachment_id': attachment_id,
                'access_token': access_token,
            }
            vaccination_list.append(data)
        values = {
            'vaccinations': vaccination_list,
            'page_name': 'vaccination'
        }
        return request.render("base_hospital_management.portal_my_vaccines",
                              values)

    @http.route(['/my/tests'], type='http', auth="public", website=True)
    def portal_my_tests(self, **kw):
        """Function for rendering tests of portal user"""
        partner_id = request.env.user.partner_id.id
        domain = ['|', ('patient_id', '=', partner_id), ('patient_id.user_ids', 'in', [request.uid])]
        tests_list = []
        for rec in request.env['patient.lab.test'].sudo().search(domain):
            request.env['account.move'].sudo().search(
                [('ref', '=', rec.test_id.name)
                 ], limit=1)
            data = {
                'id': rec.id,
                'name': rec.test_id.name,
                'date': rec.date
            }
            tests_list.append(data)
        values = {
            'tests': tests_list,
            'page_name': 'lab_test'
        }
        return request.render("base_hospital_management.portal_my_tests",
                              values)

    @http.route('/my/tests/<int:test_id>', type="http", auth="public",
                website=True)
    def tests_view(self, test_id):
        """Function for rendering test results of portal user"""
        all_test = request.env['patient.lab.test'].sudo().browse(test_id)
        if not all_test.exists():
            return request.redirect('/my/tests')
        partner_id = request.env.user.partner_id.id
        if all_test.patient_id.id != partner_id and request.uid not in all_test.patient_id.user_ids.ids:
            return request.redirect('/my/tests')
        result_list = []
        test_result_ids = request.env['lab.test.result'].sudo().search(
            [('id', 'in', all_test.result_ids.ids)])
        for rec in test_result_ids:
            attachment = request.env['ir.attachment'].sudo().search([
                ('res_id', '=', rec.id),
                ('res_model', '=', 'lab.test.result')
            ], limit=1)
            attachment_id = attachment.id if attachment else False
            access_token = ''
            if attachment:
                if not attachment.access_token:
                    attachment.generate_access_token()
                access_token = attachment.access_token or ''
            result_list.append({
                'id': rec.id,
                'name': rec.test_id.name,
                'result': rec.result,
                'price': rec.price,
                'attachment_id': attachment_id,
                'access_token': access_token,
            })
        values = {
            'all_test_id': all_test.id,
            'results': result_list,
            'page_name': 'test_results'
        }
        return request.render(
            "base_hospital_management.portal_my_tests_results", values)

    @http.route('/my/op', type='http', auth="public",
                website=True)
    def portal_my_op(self, **kw):
        """Function for rendering prescriptions of portal user"""
        partner_id = request.env.user.partner_id.id
        domain = ['|', ('patient_id', '=', partner_id), ('patient_id.user_ids', 'in', [request.uid])]
        op = request.env['hospital.outpatient'].sudo().search_read(
            domain,
            ['op_reference', 'op_date', 'doctor_id', 'slot',
             'prescription_ids'])
        for record in op:
            hours = int(record['slot'])
            minutes = int((record['slot'] - hours) * 60)
            record['slot'] = '{:02d}:{:02d}'.format(hours, minutes)
        values = {
            'op': op,
            'page_name': 'op'
        }
        return request.render(
            "base_hospital_management.portal_my_op", values)

    @http.route('/my/op/prescription/download', type='jsonrpc', auth="user")
    def portal_download_prescription(self, op_id):
        """Generates prescription and returns download url for portal user"""
        op = request.env['hospital.outpatient'].sudo().browse(int(op_id))
        if not op.exists():
            return {'error': 'Record not found'}
        partner_id = request.env.user.partner_id.id
        if op.patient_id.id != partner_id and request.uid not in op.patient_id.user_ids.ids:
            return {'error': 'Unauthorized'}
        return op._create_prescription_file()
