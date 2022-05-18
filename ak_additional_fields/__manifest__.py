
{
    'name': "Additonal fields and constraints for yeslam",
    'version': "15.0.0.0",
    'summary': "additional fields and constraints",
    'category': 'Extra Addons',
    'description': """
        this app will add alternative name and code to partners
        and Reference,Barcode, and HS Code to Products
    """,
    'author': "Expertsintech",
    'website':"www.expertsintech.com",
    'depends': ['base','stock','sale'],
    'data': [
    'views/customer_search.xml',
    'views/confirm_sale.xml',
    'views/extra_account_fields.xml',




    ],
    'demo': [],
    "external_dependencies": {},
    "license": "AGPL-3",
    'installable': True,
    'auto_install': False,

}
