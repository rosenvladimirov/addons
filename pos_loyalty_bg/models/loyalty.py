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

class loyalty_program(models.Model):
    _name = 'loyalty.program'
    _description = 'Loyalty program for sales'

    name = fields.Char(string="Loyalty Program Name", select=True, required=True, help="An internal identification for the loyalty program configuration")
    pp_currency = fields.Float(string='Points per currency',help="How many loyalty points are given to the customer by sold currency")
    pp_product = fields.Float(string='Points per product',help="How many loyalty points are given to the customer by product sold")
    pp_order = fields.Float(string='Points per order',help="How many loyalty points are given to the customer for each sale or order")
    rounding = fields.Float(string='Points Rounding', default=1, help="The loyalty point amounts are rounded to multiples of this value.")
    rule_ids = fields.One2many(string="Rules", comodel_name="loyalty.rule", inverse_name="loyalty_program_id")
    reward_ids = fields.One2many(string="Rules", comodel_name="loyalty.reward", inverse_name="loyalty_program_id")

    @api.model
    def calculate_loyalty_points(self, product, qty, price):
        for rule in self.rule_ids.sorted(lambda r: r.sequence):
            if rule.check_match(product, qty, price):
                return rule.calculate_points(product, qty, price)
        return 0

class loyalty_rule(models.Model):
    _name = 'loyalty.rule'
    _description = 'Loyalty rules'

    @api.one
    @api.depends('product_id', 'category_id')
    def _compute_type(self):
        return ((not self.product_id and self.category_id) and 'category' or 'product')

    name = fields.Char(string="Name", select=True, required=True, help="An internal identification for this loyalty program rule")
    loyalty_program_id = fields.Many2one(comodel_name='loyalty.program',string='Loyalty Program', help='The Loyalty Program this reward belongs to')
    type = fields.Char(string="Type of Loyalty Rule",compute="_compute_type", help="Differend type of lloyalty rules (product or category)")
    product_id = fields.Many2one(comodel_name='product.product',string='Target Product', help='The product affected by the rule')
    category_id = fields.Many2one(comodel_name='product.category',string='Target Category', help='The category affected by the rule')
    cumulative = fields.Boolean(string="Cumulative", help='How many points the product will earn per product ordered')
    sequence = fields.Integer(string='Sequence', default=100)
    pp_product = fields.Integer(string="Points per product",  help="How many points the product will earn per product ordered")
    pp_currency = fields.Integer(string="Points per currency", help="How many points the product will earn per value sold")

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
        return self.product_points * qty + self.pp_currency * price

class loyalty_reward(models.Model):
    _name = 'loyalty.reward'

    name = fields.Char(string="Name", select=True, required=True, help="An internal identification for this loyalty reward")
    loyalty_program_id = fields.Many2one(string="Loyalty Program", comodel_name="loyalty.program", help="The Loyalty Program this reward belongs to")
    minimum_points = fields.Integer(string="Minimum Points", help="The minimum amount of points the customer must have to qualify for this reward")
    type = fields.Selection(string="Type", selection=[("gift","Gift"),("discount","Discount"),("resale","Resale")], help="The type of the reward")
    gift_product_id = fields.Many2one(string="Gift Product", comodel_name="product.product", help="The product given as a reward")
    point_cost = fields.Integer(string="Point Cost", help="The cost of the reward per monetary unit discounted")
    discount_product_id = fields.Many2one(string="Discount Product", comodel_name="product.product", help="The product used to apply discounts")
    discount = fields.Float(string="Discount", help="The discount percentage")
    point_product_id = fields.Many2one(string="Point Product", comodel_name="product.product", help="The product that represents a point that is sold by the customer")
    image = fields.Binary(help='Show Image Category in Form View')
    image_medium = fields.Binary(help='Show image category button in POS',
                                 compute="_get_image",
                                 inverse="_set_image",
                                 store=True)

    @api.multi
    def _get_image(self):
        return dict(
            (rec.id, tools.image_get_resized_images(rec.image)) for rec in
            self)

    @api.one
    def _set_image(self):
        return self.write(
            {'image': tools.image_resize_image_big(self.image_medium)})

    @api.multi
    @api.constrains("type", "gift_product_id")
    def _check_gift_product(self):
        for reward in self:
            if reward.type == 'gift':
                return bool(reward.gift_product_id)
            else:
                return True

    @api.multi
    @api.constrains("type", "discount_product_id")
    def _check_discount_product(self):
        for reward in self:
            if reward.type == 'discount':
                return bool(reward.discount_product_id)
            else:
                return True

    @api.multi
    @api.constrains("type", "discount_product_id")
    def _check_point_product(self):
        for reward in self:
            if reward.type == 'resale':
                return bool(reward.discount_product_id)
            else:
                return True

