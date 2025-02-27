# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api

module_list = ['shopify_ept', 'woo_commerce_ept', 'amazon_ept', 'walmart_ept', 'ebay_ept', 'bol_ept']


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ept_image_ids = fields.One2many('common.product.image.ept', 'template_id', string='Product Images')

    def prepare_template_common_image_vals(self, vals):
        """
        Define this method for prepares vals for creating common product image record.
        :param: vals: dict {}
        :return: dict {}
        """
        image_vals = {"sequence": 0,
                      "image": vals.get("image_1920", False),
                      "name": self.name,
                      "template_id": self.id}
        return image_vals

    @api.model_create_multi
    def create(self, vals_list):
        """
        Inherited this method for adding the main image in common images.
        :param: vals_list : list of dict {}
        :return: product.template()
        """
        product_obj = self.env['product.product']
        installed_module = False
        res = super(ProductTemplate, self).create(vals_list)
        for key in module_list:
            if product_obj.search_installed_module_ept(key):
                if not installed_module:
                    installed_module = True
                    for vals in vals_list:
                        if vals.get("image_1920", False) and res:
                            image_vals = res.prepare_template_common_image_vals(vals)
                            self.env["common.product.image.ept"].with_context(main_image=True).create(image_vals)
        return res

    def write(self, vals):
        """
        Inherited this method for adding the main image in common images.
        :param: vals: dict {}
        :return: True/False
        """
        product_obj = self.env['product.product']
        installed_module = False
        res = super(ProductTemplate, self).write(vals)
        for key in module_list:
            if product_obj.search_installed_module_ept(key):
                if not installed_module:
                    installed_module = True
                    if vals.get("image_1920", False) and self:
                        common_product_image_obj = self.env["common.product.image.ept"]
                        for record in self:
                            if self.image_1920:
                                common_product_image = self.ept_image_ids.filtered(
                                    lambda x: x.image == self.image_1920)
                                if common_product_image:
                                    return True
                            if vals.get("image_1920"):
                                image_vals = record.prepare_template_common_image_vals(vals)
                                common_product_image_obj.with_context(main_image=True).create(image_vals)
        return res
