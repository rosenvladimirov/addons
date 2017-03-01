# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from openerp import api, models, fields, exceptions, _
import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    @api.v7
    def _price_rule_get_multi_ex(self, cr, uid, query, query_arg, products, context=None):
        #query, query_arg = super(ProductPricelist,self)._price_rule_get_multi_ex(self, cr, uid, query, query_arg, products, context=context)
        mc_ids = {}
        for p in products:
            if (p.margin_classification_id.id):
                mc_ids[p.margin_classification_id.id] = True
        mc_ids = mc_ids.keys()
        if not mc_ids:
            return query, query_arg
        query = """SELECT i.id 
                    FROM product_pricelist_item AS i 
                    WHERE (product_tmpl_id IS NULL OR product_tmpl_id = any(%(prod_tmpl_ids)s)) 
                        AND (product_id IS NULL OR (product_id = any(%(prod_ids)s))) 
                        AND ((categ_id IS NULL) OR (categ_id = any(%(categ_ids)s))) 
                        AND ((margin_classification_id IS NULL) OR (margin_classification_id = any(%(mc_ids)s))) 
                        AND (price_version_id = %(version_id)s) 
                    ORDER BY sequence, min_quantity desc"""
        query_arg = dict(query_arg or {}, mc_ids=mc_ids)
        #_logger.info('Recreate price list items searsh->query: %s arg: %s' % (query, query_arg))
        return query, query_arg

    @api.v7
    def _price_rule_get_multi_ex_rule(self, cr, uid, rule, products, context=None):
        mc_ids = {}
        for p in products:
            if (p.margin_classification_id.id):
                mc_ids[p.margin_classification_id.id] = True
        mc_ids = mc_ids.keys()
        #_logger.info("Ex rule %s:%s" % (mc_ids, rule))
        if not mc_ids:
            return False
        if (mc_ids[0] != rule.margin_classification_id.id):
            return True
        return False

class ProductPricelistVersion(models.Model):
    _inherit = "product.pricelist.version"

    pricelist_visable = fields.Boolean(string='Visiable in documents',
                                    help="Chek it if like to show in documents and partner form.")

class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    margin_classification_id = fields.Many2one(comodel_name='product.margin.classification',
                                               string='Margin Classification', 
                                               ondelete='cascade', 
                                               help="Specify a Margin Classification category if this rule only applies to products belonging to this category or its children categories. Keep empty otherwise.")
    margin_classification_discount = fields.Float(string='Percent by discount',
                                                  digits_compute=dp.get_precision('Product Price'),
                                                  help="Specify the percent amount from discount an  the amount calculated with the discount.")

    @api.onchange('margin_classification_id','base_pricelist_id','margin_classification_discount')
    def onchange_mc(self):
        self.ensure_one()
        mc = self.env['product.margin.classification'].browse(self.margin_classification_id.id)
        #_logger.info("On change %s:%s" % (mc,self.margin_classification_id.id))
        if mc:
            self.price_min_margin = 0
            self.price_max_margin = (mc.margin/100)
            self.price_discount = ((mc.margin)*(self.margin_classification_discount/100)*-1)/100

    @api.multi
    @api.depends('price_max_margin', 'price_discount','margin_classification_discount')
    def update_margin_mc(self, margin):
        _logger.info("Recive a new margin %s:%s" % (margin,self))
        for item in self:
            item.price_max_margin = (margin/100)
            item.price_discount = ((margin)*(item.margin_classification_discount/100)*-1)/100
            _logger.info("Update new margin %s:%s"% (item.price_max_margin, item.price_discount))
