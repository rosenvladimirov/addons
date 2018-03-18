# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, fields, api, _

class CreditControlPolicyLevel(models.Model):
    _inherit = "credit.control.policy.level"

    channel = fields.Selection(selection_add=[('internal_letter', 'internal letter for temporary permit'), ('phone', 'Phone Call')])
