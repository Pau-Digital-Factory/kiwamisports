from odoo import api, fields, models, tools, _
from odoo.osv import expression
from odoo.exceptions import AccessError









class ShopifyProductTemplateEptt(models.Model):
    _inherit = "shopify.product.template.ept"

    def prepare_variant_vals(self, instance, variant_data):
        """
        This method used to prepare a shopify variant dictionary.
        @param instance:
        @param variant_data: Data of Shopify variant.
        @author: Maulik Barad on Date 01-Sep-2020.
        """
        variant_vals = {"shopify_instance_id": instance.id,
                        "variant_id": variant_data.get("id"),
                        "sequence": variant_data.get("position"),
                        "default_code": variant_data.get("sku", ""),
                        "hs_code": variant_data.get("harmonizedSystemCode"),
                        "inventory_item_id": variant_data.get("inventory_item_id"),
                        "inventory_management": "shopify" if variant_data.get(
                            "inventory_management") == "shopify" else "Dont track Inventory",
                        "check_product_stock": variant_data.get("inventory_policy"),
                        "taxable": variant_data.get("taxable"),
                        "created_at": self.convert_shopify_date_into_odoo_format(variant_data.get("created_at")),
                        "updated_at": self.convert_shopify_date_into_odoo_format(variant_data.get("updated_at")),
                        "exported_in_shopify": True,
                        "active": True}

        return variant_vals