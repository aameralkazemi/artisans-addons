# -*- coding: utf-8 -*-
{
    "name": "Universal Appointments: Sales",
    "version": "15.0.1.0.2",
    "category": "Sales",
    "author": "faOtools",
    "website": "https://faotools.com/apps/15.0/universal-appointments-sales-612",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "business_appointment",
        "sale_management"
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/business_resource_type.xml",
        "views/business_appointment.xml",
        "reports/appointment_analytic.xml"
    ],
    "assets": {},
    "demo": [
        
    ],
    "external_dependencies": {},
    "summary": "The extension to the Universal Appointments app to link appointments and sale orders",
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
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=131&ticket_version=15.0&url_type_id=3",
}