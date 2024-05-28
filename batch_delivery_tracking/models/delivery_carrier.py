# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana kp(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
import logging
from markupsafe import Markup
from zeep.helpers import serialize_object
from odoo import models, _
from odoo.exceptions import UserError
from odoo.tools import pdf
from odoo.addons.delivery_fedex.models.fedex_request import FedexRequest, \
  _convert_curr_iso_fdx

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    """This class inherits from the base delivery carrier model and
    allows for additional customization and functionality to be added
    to delivery carriers. """
    _inherit = "delivery.carrier"

    def fedex_send_shipping(self, picking):
        """Overriding default fedex integration function to
        check with our condition"""
        if picking.batch_id and not picking.carrier_tracking_ref:
            partner_id = picking.partner_id.id
            carrier_id = picking.carrier_id.id
            filtered_picking_ids = picking.batch_id.picking_ids.filtered(
                lambda
                    x: x.partner_id.id == partner_id and x.carrier_id.id == carrier_id)
            # Now you have filtered_picking_ids with the desired records
            if len(filtered_picking_ids) > 1:
                response = self._batch_fedex_send_shipping(picking,
                                                           filtered_picking_ids)
                return response
            else:
                res = super().fedex_send_shipping(picking)
                return res
        else:
            res = super().fedex_send_shipping(picking)
            return res

    def _batch_fedex_send_shipping(self, picking, filtered_picking_ids):
        """ Function for batch transfers picking to connect fedex and return
        same tracking numbers for all picking with same
        carrier id and customer. """
        res = []
        order_currency = picking.sale_id.currency_id or picking.company_id.currency_id
        srm = FedexRequest(self.log_xml, request_type="shipping",
                           prod_environment=self.prod_environment)
        superself = self.sudo()
        srm.web_authentication_detail(superself.fedex_developer_key,
                                      superself.fedex_developer_password)
        srm.client_detail(superself.fedex_account_number,
                          superself.fedex_meter_number)
        srm.transaction_detail(picking.id)
        package_type = picking.package_ids and picking.package_ids[
            0].package_type_id.shipper_package_code or self.fedex_default_package_type_id.shipper_package_code
        srm.shipment_request(self.fedex_droppoff_type, self.fedex_service_type,
                             package_type, self.fedex_weight_unit,
                             self.fedex_saturday_delivery)
        srm.set_currency(_convert_curr_iso_fdx(order_currency.name))
        srm.set_shipper(picking.company_id.partner_id,
                        picking.picking_type_id.warehouse_id.partner_id)
        srm.set_recipient(picking.partner_id)
        srm.shipping_charges_payment(superself.fedex_account_number)
        srm.shipment_label('COMMON2D', self.fedex_label_file_type,
                           self.fedex_label_stock_type,
                           'TOP_EDGE_OF_TEXT_FIRST', 'SHIPPING_LABEL_FIRST')
        order = picking.sale_id
        net_weight = 0.0
        if 'INTERNATIONAL' in self.fedex_service_type or self.fedex_service_type == 'FEDEX_REGIONAL_ECONOMY' or (
                picking.partner_id.country_id.code == 'IN' and picking.picking_type_id.warehouse_id.partner_id.country_id.code == 'IN'):
            commodities = self._get_commodities_from_stock_move_lines(
                picking.move_line_ids)
            for commodity in commodities:
                srm.commodities(self, commodity,
                                _convert_curr_iso_fdx(order_currency.name))

            total_commodities_amount = sum(
                c.monetary_value * c.qty for c in commodities)
            srm.customs_value(_convert_curr_iso_fdx(order_currency.name),
                              total_commodities_amount, "NON_DOCUMENTS")
            srm.duties_payment(order.warehouse_id.partner_id,
                               superself.fedex_account_number,
                               superself.fedex_duty_payment)
            send_etd = superself.env['ir.config_parameter'].get_param(
                "delivery_fedex.send_etd")
            srm.commercial_invoice(self.fedex_document_stock_type, send_etd)
        package_count = 1
        packages = []
        package_ids = []
        for pick in filtered_picking_ids:
            if not pick.carrier_tracking_ref:
                if pick.package_ids not in package_ids:
                    package_ids.append(pick.package_ids)
                    converted_weight = self._fedex_convert_weight(
                        pick.shipping_weight, self.fedex_weight_unit)
                    package_count += len(pick.package_ids)
                    package = self._get_packages_from_picking(pick,
                                                              self.fedex_default_package_type_id)
                    packages.append(package)
        if isinstance(converted_weight, (int, float)):
            net_weight += converted_weight
        po_number = order.display_name or False
        dept_number = False
        if picking.partner_id.country_id.code == 'IN' and picking.picking_type_id.warehouse_id.partner_id.country_id.code == 'IN':
            po_number = 'B2B' if picking.partner_id.commercial_partner_id.is_company else 'B2C'
            dept_number = 'BILL D/T: SENDER'
        master_tracking_id = False
        package_labels = []
        carrier_tracking_refs = []
        flattened_packages = [item for sublist in packages for item in sublist]
        for sequence, package in enumerate(flattened_packages, start=1):
            srm.add_package(
                self,
                package,
                _convert_curr_iso_fdx(package.company_id.currency_id.name),
                sequence_number=sequence,
                po_number=po_number,
                dept_number=dept_number,
                reference=picking.display_name,
            )
            srm.set_master_package(net_weight, len(flattened_packages),
                                   master_tracking_id=master_tracking_id)
            self._fedex_update_srm(srm, 'ship', picking=picking)
            request = serialize_object(
                dict(WebAuthenticationDetail=srm.WebAuthenticationDetail,
                     ClientDetail=srm.ClientDetail,
                     TransactionDetail=srm.TransactionDetail,
                     VersionId=srm.VersionId,
                     RequestedShipment=srm.RequestedShipment))
            self._fedex_add_extra_data_to_request(request, 'ship')
            response = srm.process_shipment(request)
            warnings = response.get('warnings_message')
            if warnings:
                _logger.info(warnings)
            if response.get('errors_message'):
                raise UserError(response['errors_message'])
            package_name = package.name or 'package-' + str(sequence)
            package_labels.append((package_name, srm.get_label()))
            carrier_tracking_refs.append(response['tracking_number'])
            if sequence == 1:
                master_tracking_id = response['master_tracking_id']
            # Last package
            if sequence == len(flattened_packages):
                carrier_price = self._get_request_price(response['price'],
                                                        order,
                                                        order_currency)
                if self.fedex_label_file_type != 'PDF':
                    attachments = [('%s-%s.%s' % (
                        self._get_delivery_label_prefix(), pl[0],
                        self.fedex_label_file_type), pl[1]) for pl in
                                   package_labels]
                if self.fedex_label_file_type == 'PDF':
                    attachments = [
                        ('%s.pdf' % (self._get_delivery_label_prefix()),
                         pdf.merge_pdf(
                             [pl[1] for pl in package_labels]))]
                num = 0
                for pick in filtered_picking_ids:
                    if not pick.carrier_tracking_ref and num < len(
                            carrier_tracking_refs):
                        logmessage = Markup(
                            _("Shipment created into Fedex<br/>"
                              "<b>Tracking Numbers:</b> %s<br/>"
                              "<b>Packages:</b> %s")) % (
                                         carrier_tracking_refs[num],
                                         pick.package_ids.name)
                        num += 1
                        pick.message_post(body=logmessage,
                                          attachments=attachments)
                shipping_data = {'exact_price': carrier_price,
                                 'tracking_number': ','.join(
                                     carrier_tracking_refs)}
                res = res + [shipping_data]
                logmessage = Markup(_("Shipment created into Fedex<br/>"
                                      "<b>Tracking Numbers:</b> %s<br/>"
                                      "<b>Packages:</b> %s")) % (
                                 ','.join(carrier_tracking_refs),
                                 ','.join([pl[0] for pl in package_labels]))
                if self.fedex_label_file_type != 'PDF':
                    attachments = [('%s-%s.%s' % (
                        self._get_delivery_label_prefix(), pl[0],
                        self.fedex_label_file_type), pl[1]) for pl in
                                   package_labels]
                if self.fedex_label_file_type == 'PDF':
                    attachments = [('%s.pdf' % (
                        self._get_delivery_label_prefix()), pdf.merge_pdf(
                        [pl[1] for pl in package_labels]))]
                picking.batch_id.message_post(body=logmessage,
                                              attachments=attachments)
        return res
