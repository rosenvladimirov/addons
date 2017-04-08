# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging

from openerp import models, fields, tools, api
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

class PosConfig(models.Model):
    _inherit = 'pos.config'
    loyalty_id = fields.Many2one(string="Loyalty Program", comodel_name="loyalty.program", help="The loyalty program used by this point_of_sale")

class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    @api.one
    @api.depends('product_id', 'qty', 'price_subtotal', 'order_id.loyalty_program_id')
    def _loyalty_points(self):
        if self.order_id.loyalty_program_id:
            self.loyalty_points = self.order_id.loyalty_program_id.calculate_loyalty_points(self.product_id, self.qty, self.price_subtotal)
    loyalty_points = fields.Integer(string='Loyalty Points', compute='_loyalty_points', store=False)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.one
    @api.depends('lines', 'lines.product_id', 'lines.qty', 'lines.price_subtotal')
    def _loyalty_points(self):
        self.loyalty_points = sum([l.loyalty_points for l in self.lines])
    loyalty_points_compute = fields.Integer(string='Loyalty Points Computed', compute='_loyalty_points', store=False, help="The amount of Loyalty points the customer won or lost with this order")
    loyalty_points = fields.Integer(string='Loyalty Points', help="The amount of Loyalty points the customer won or lost with this order")
    loyalty_program_id = fields.Many2one(comodel_name='loyalty.program', string='Loyalty Program')

    # Overload Section
    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res['loyalty_points'] = ui_order.get('loyalty_points',0)
        return res

    @api.model
    def create_from_ui(self, orders):
        ids = super(PosOrder, self).create_from_ui(orders)
        for order in orders:
            _logger.info('orders: %s' % order)
            if order['data']['loyalty_points'] != 0 and order['data']['partner_id']:
                partner = self.env['res.partner'].browse(order['data']['partner_id'])
                loyalty_points = partner.sale_loyalty_points + partner.loyalty_points + order['data']['loyalty_points']
                partner.write({'loyalty_points': loyalty_points})
        return ids
