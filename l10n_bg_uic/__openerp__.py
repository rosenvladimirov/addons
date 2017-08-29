# -*- coding: utf-8 -*-
#
# © 2004-2010 Tiny SPRL http://tiny.be
# © 2010-2012 ChriCar Beteiligungs- und Beratungs- GmbH
#             http://www.camptocamp.at
# © 2015 Antiun Ingenieria, SL (Madrid, Spain)
#        http://www.antiun.com
#        Antonio Espinosa <antonioea@antiun.com>
# © 2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Partner Unique Identification Numbers',
    'category': 'Customer Relationship Management',
    'version': '8.0.1.0.0',
    'data': [
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
        'data/res_partner_category_id.xml',
    ],
    'depends': [
        'account',
        'partner_identification_bg',
    ],
    'author': 'Odoo Community Association (OCA), '
              'Rosen Vladimirov',
    'website': 'https://odoo-community.org/',
    'license': 'AGPL-3',
    'installable': True,
    #'post_init_hook': 'post_init_hook',
}
