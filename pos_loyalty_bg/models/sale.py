# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2015 Vertel AB (<http://vertel.se>).
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
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger(__name__)

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    @api.one
    @api.depends('product_id', 'product_uom_qty', 'price_subtotal', 'order_id.loyalty_program_id')
    def _loyalty_points(self):
        _logger.info("Sale order lines %s" % self.order_id.loyalty_program_id)
        if self.order_id.loyalty_program_id:
            self.loyalty_points = self.order_id.loyalty_program_id.calculate_loyalty_points(self.product_id, self.product_uom_qty, self.price_subtotal)
    loyalty_points = fields.Integer(string='Loyalty Points', compute='_loyalty_points', store=True)

class sale_order(models.Model):
    _inherit = 'sale.order'

    loyalty_program_id = fields.Many2one(comodel_name='loyalty.program', string='Loyalty Program')
    @api.one
    @api.depends('order_line', 'order_line.product_id', 'order_line.product_uom_qty', 'order_line.price_subtotal')
    def _loyalty_points(self):
        _logger.info("Sale order take %s" % self.order_line)
        self.loyalty_points = sum([l.loyalty_points for l in self.order_line])
    loyalty_points = fields.Integer(string='Loyalty Points', compute='_loyalty_points', store=True)
