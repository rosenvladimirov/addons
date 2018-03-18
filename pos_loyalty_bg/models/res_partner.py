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

class ResPartner(models.Model):
    _inherit = 'res.partner'

    #@api.one
    #def _loyalty_points(self):
    #    self.loyalty_points = sum([o.loyalty_points for o in self.sale_order_ids.filtered(lambda o: o.state == 'done' and o.date_order > (datetime.today() - relativedelta(years=1)).strftime('%Y%m%d'))])
    #    self.loyalty_points += sum([child.loyalty_points for child in self.child_ids])
    #sale_loyalty_points = fields.Integer(string='Loyalty Points',compute="_loyalty_points", store=False, help="The loyalty points the user won as part of a Loyalty Program")
    loyalty_points = fields.Integer('Loyalty Points', help='The loyalty points the user won as part of a Loyalty Program')
