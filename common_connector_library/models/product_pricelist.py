# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models


class ProductPriceList(models.Model):
    _inherit = "product.pricelist"

    def set_product_price_ept(self, product_id, price, min_qty=1):
        """
        Define this method for create or update price in the pricelist.
        :param: product_id: product.product() id
        :param: price: float:
        :param: min_qty: float
        :return: product.pricelist.item()
        """
        price_list_item_obj = self.env['product.pricelist.item']
        price_list_item = price_list_item_obj.search([('pricelist_id', '=', self.id),
                                                      ('product_id', '=', product_id), ('min_quantity', '=', min_qty)])
        if price_list_item:
            price_list_item.write({'fixed_price': price})
            price_list_item.invalidate_model(['fixed_price'])
        else:
            vals = self.prepre_pricelistitem_vals(product_id, min_qty, price)
            new_record = price_list_item_obj.new(vals)
            new_record._onchange_product_id()
            new_vals = price_list_item_obj._convert_to_write(
                {name: new_record[name] for name in new_record._cache})
            price_list_item = price_list_item_obj.create(new_vals)
        return price_list_item

    def prepre_pricelistitem_vals(self, product_id, min_qty, price):
        """
        Define this method for prepare values for price list item.
        :param: product_id: product.product() id
        :param: min_qty: float
        :param: price: float
        :return: dict {}
        """
        vals = {
            'pricelist_id': self.id,
            'applied_on': '0_product_variant',
            'product_id': product_id,
            'min_quantity': min_qty,
            'fixed_price': price,
        }
        return vals

    # def get_product_price_list_rule(self, product, quantity, partner):
    #     """
    #     Define this method for get price list rule base on given product.
    #     :param: product: product.product()
    #     :param: quantity: float
    #     :param: partner:
    #     return: pricelist rule
    #     """
    #     rule = self._get_product_price_rule(product, quantity, partner, date=False, uom_id=product.uom_id.id)
    #     return rule
