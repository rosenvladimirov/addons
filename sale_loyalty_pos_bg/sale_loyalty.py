# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2016 Vertel AB (<http://vertel.se>).
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



class pos_order_line(models.Model):
    _inherit = 'pos.order.line'
    
    @api.one
    @api.depends('product_id', 'qty', 'price_subtotal', 'order_id.loyalty_program_id')
    def _loyalty_points(self):
        if self.order_id.loyalty_program_id:
            self.loyalty_points = self.order_id.loyalty_program_id.calculate_loyalty_points(self.product_id, self.qty, self.price_subtotal)
    loyalty_points = fields.Integer(string='Loyalty Points', compute='_loyalty_points', store=True)
    
class pos_order(models.Model):
    _inherit = 'pos.order'
    
    loyalty_program_id = fields.Many2one(comodel_name='loyalty.program',related="partner_id.loyalty_program_id")
    @api.one
    @api.depends('lines', 'lines.product_id', 'lines.qty', 'lines.price_subtotal')
    def _loyalty_points(self):
        self.loyalty_points = sum([l.loyalty_points for l in self.lines])
    loyalty_points = fields.Integer(string='Loyalty Points', compute='_loyalty_points', store=True)

class res_partner(models.Model):
    _inherit = 'res.partner'
    
    @api.one
    def _loyalty_points(self):
        super(res_partner,self)._loyalty_points()
        self.loyalty_points += sum([p.loyalty_points for p in self.pos_order_ids])
        #~ self.loyalty_points += sum([p.loyalty_points for p in child.pos_order_ids] for child in self.child_ids)
        self.loyalty_points += sum([p.loyalty_points for child in self.child_ids for p in child.pos_order_ids])

