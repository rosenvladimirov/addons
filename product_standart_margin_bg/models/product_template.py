# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2012 Camptocamp SA (http://www.camptocamp.com)
#    All Right Reserved
#
#    Author : Joel Grand-Guillaume
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

from openerp import fields, api
from openerp.models import Model
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(Model):
    _inherit = 'product.template'

    @api.multi
    @api.depends('list_price', 'standard_price')
    def _get_margin(self):
        for product in self:
            #_logger.info("Prices %s:%s" % (product.list_price, product.standard_price))
            product.standard_margin =\
                product.list_price - product.standard_price
            if product.standard_price != 0.0:
                product.standard_margin_rate = ((product.list_price/product.standard_price) -1)*100
            else:
                product.standard_margin_rate = 0

    # Column Section
    standard_margin = fields.Float(
        compute=_get_margin, string='Theorical Margin', store=True,
        digits_compute=dp.get_precision('Product Price'),
        help='Theorical Margin is [ sale price (Wo Tax) - cost price ] '
             'of the product form (not based on historical values). '
             'Take care of tax include and exclude. If no sale price, '
             'the margin will be negativ.')

