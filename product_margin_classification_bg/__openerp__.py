# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Product Margin Classification fix',
    'version': '8.0.1.0.0',
    'category': 'Account',
    'author': 'Rosen Vladimirov,GRAP,Odoo Community Association (OCA)',
    'website': 'http://www.grap.coop.xml',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'purchase',
    ],
    'data': [
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'views/view_product_template.xml',
        'views/view_product_margin_classification.xml',
        'views/pricelist_view.xml',
        'views/partner_view.xml',
        'views/purchase.xml',
        'views/action.xml',
        'views/menu.xml',
        #'wizard/product_margin_classification_check.xml',
    ],
    'demo': [
        'demo/res_groups.yml',
        'demo/product_margin_classification.xml',
        'demo/product_template.xml',
    ],
    'installable': True,
}
