# -*- coding: utf-8 -*-
{
    "name": "Universal Appointments: Website Sales",
    "version": "15.0.1.0.1",
    "category": "Website",
    "author": "faOtools",
    "website": "https://faotools.com/apps/15.0/universal-appointments-website-sales-614",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "business_appointment_website",
        "business_appointment_sale",
        "website_sale"
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/res_config_settings.xml",
        "views/full_details_templates.xml",
        "views/templates.xml",
        "views/portal_templates.xml"
    ],
    "assets": {},
    "demo": [
        
    ],
    "external_dependencies": {},
    "summary": "The extension to the Universal Appointments app to show service prices on website",
    "description": """
For the full details look at static/description/index.html

* Features * 




#odootools_proprietary

    """,
    "images": [
        "static/description/main.png"
    ],
    "price": "0.0",
    "currency": "EUR",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=132&ticket_version=15.0&url_type_id=3",
}