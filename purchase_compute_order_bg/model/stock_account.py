# -*- encoding: utf-8 -*-
##############################################################################
#
#    Purchase - Computed Purchase Order Module for Odoo
#    Copyright (C) 2013-Today GRAP (http://www.grap.coop)
#    @author Julien WESTE
#    @author Sylvain LE GAL (https://twitter.com/legalsylvain)
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

from openerp import models, api, fields
import openerp.addons.decimal_precision as dp
from openerp import SUPERUSER_ID, api

import logging
_logger = logging.getLogger(__name__)

class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.cr_uid_ids_context
    def _account_entry_move_ex(self, cr, uid, parts, context=None):
        parts = super(StockQuant, self)._account_entry_move_ex(cr, uid, parts, context=context)
        _logger.debug("Averashe standart price старт %s=>%s" % (parts['move'].product_id.product_tmpl_id.seller_ids, context))
        #product_obj = self.pool.get('product.product')
        product_supplierinfo_obj = self.pool.get('product.supplierinfo')
        pricelist_partnerinfo_obj = self.pool.get('pricelist.partnerinfo')
        move = parts['move']
        company_from = parts['location_from'].partner_id
        company_to = parts['company_to']
        if company_from and company_to and (move.location_id.usage not in ('internal', 'transit') and move.location_dest_id.usage == 'internal' or company_from != company_to):
            #ctx = context.copy()
            #ctx['force_company'] = company_to.id
            #ctx['name'] = company_from.id
            #ctx['product_tmpl_id'] = move.product_id.product_tmpl_id.id
            s_ids = product_supplierinfo_obj.search(cr, uid, [('name','=',company_from.id),('product_tmpl_id', '=', move.product_id.product_tmpl_id.id)], context=context)
            for product_supplierinfo in product_supplierinfo_obj.browse(cr, uid, s_ids, context=context):
            #for product_supplierinfo in product_supplierinfo_obj.browse(cr, uid, [move.product_id.product_tmpl_id.seller_ids], context=ctx):
                _logger.debug("Averashe standart price %s:%s:%s" % (company_from, company_to, product_supplierinfo))
                if len(product_supplierinfo.pricelist_ids) > 0:
                    for pricelist_partnerinfo in pricelist_partnerinfo_obj.browse(cr, uid, product_supplierinfo.pricelist_ids.id, context=context):

                        if pricelist_partnerinfo.min_quantity == 0.0:
                            pricelist_partnerinfo.write({'price': move.price_unit})
                            break
                else:
                    pricelist_partnerinfo_obj.create(cr, uid, {"suppinfo_id": product_supplierinfo.id, "min_quantity": 0.0, "name": "Add from purchase order", "price": move.price_unit}, context=context)
            #    product_supplierinfo.price = move.price_unit
        return parts
