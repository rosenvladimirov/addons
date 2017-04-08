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

class loyalty_program(models.Model):
    _name = 'loyalty.program'
    
    name = fields.Char('Name', select=True, required=True)
    #rounding = fields.Float('Points Rounding')
    rule_ids = fields.One2many('loyalty.rule','loyalty_program_id','Rules')
    reward_ids = fields.One2many('loyalty.reward','loyalty_program_id','Rewards')
    
    @api.model
    def calculate_loyalty_points(self, product, qty, price):
        for rule in self.rule_ids.sorted(lambda r: r.sequence):
            if rule.check_match(product, qty, price):
                return rule.calculate_points(product, qty, price)
        return 0
    

class loyalty_rule(models.Model):
    _name = 'loyalty.rule'
    
    name = fields.Char('Name', select=True, required=True)
    loyalty_program_id = fields.Many2one(comodel_name='loyalty.program',string='Loyalty Program')
    product_id = fields.Many2one(comodel_name='product.product',string='Target Product')
    category_id = fields.Many2one(comodel_name='product.category',string='Target Category')
    sequence = fields.Integer(string='Sequence', default=100)
    product_points = fields.Integer(string='Points per product')
    currency_points = fields.Integer(string='Points per currency')
    
    @api.multi
    def check_match(self, product, qty, price):
        self.ensure_one()
        def is_child_of(p_categ, c_categ):
            if p_categ == c_categ:
                return True
            elif not c_categ.parent_id:
                return False
            else:
                return is_child_of(p_categ, c_categ.parent_id)
        #Add quantity to rules matching?
        return (not self.product_id or self.product_id == product) and (not self.category_id or is_child_of(self.category_id, product.categ_id))
    
    @api.multi
    def calculate_points(self, product, qty, price):
        self.ensure_one()
        return self.product_points * qty + self.currency_points * price

class loyalty_reward(models.Model):
    _name = 'loyalty.reward'
    
    name = fields.Char('Name', select=True, required=True)
    loyalty_program_id = fields.Many2one(comodel_name='loyalty.program',string='Loyalty Program', help='The Loyalty Program this reward belongs to')
    type = fields.Selection([('gift','Gift'),('discount','Discount'),('resale','Resale')], string='Type', required=True)
    gift_product_id = fields.Many2one(comodel_name='product.product',string='Gift Product', help='The product given as a reward')
    point_cost = fields.Integer(string='Point Cost', help='The cost of the reward')
    discount = fields.Float(string='Discount',help='The discount percentage')

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'
    
    @api.one
    @api.depends('product_id', 'product_uom_qty', 'price_subtotal', 'order_id.loyalty_program_id')
    def _loyalty_points(self):
        if self.order_id.loyalty_program_id:
            self.loyalty_points = self.order_id.loyalty_program_id.calculate_loyalty_points(self.product_id, self.product_uom_qty, self.price_subtotal)
    loyalty_points = fields.Integer(string='Loyalty Points', compute='_loyalty_points', store=True)
    
class sale_order(models.Model):
    _inherit = 'sale.order'
    
    loyalty_program_id = fields.Many2one(comodel_name='loyalty.program', string='Loyalty Program')
    @api.one
    @api.depends('order_line', 'order_line.product_id', 'order_line.product_uom_qty', 'order_line.price_subtotal')
    def _loyalty_points(self):
        self.loyalty_points = sum([l.loyalty_points for l in self.order_line])
    loyalty_points = fields.Integer(string='Loyalty Points', compute='_loyalty_points', store=True)

class res_partner(models.Model):
    _inherit = 'res.partner'
    
    @api.one
    def _loyalty_points(self):  
        self.loyalty_points = sum([o.loyalty_points for o in self.sale_order_ids.filtered(lambda o: o.state == 'done' and o.date_order > (datetime.today() - relativedelta(years=1)).strftime('%Y%m%d'))]) - sum([p.loyalty_points for p in self.product_pricelist_ids])
        self.loyalty_points += sum([child.loyalty_points for child in self.child_ids])
    loyalty_points = fields.Integer(string='Loyalty Points',compute="_loyalty_points")
    loyalty_program_id = fields.Many2one(comodel_name='loyalty.program', string='Loyalty Program')

    product_pricelist_ids = fields.One2many(comodel_name='product.pricelist',inverse_name='partner_id')

class product_pricelist(models.Model):
    _inherit = "product.pricelist"
    
    loyalty_points = fields.Integer(string='Loyalty Points')
    partner_id = fields.Many2one(comodel_name='res.partner')
    