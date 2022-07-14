# -*- coding: utf-8 -*-
##########################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
##########################################################################
{
    "name":  "Msegat SMS Gateway",
    "summary":  """Send sms notifications using Msegat SMS Gateway.""",
    "category":  "Marketing",
    "version":  "1.0.1",
    "sequence":  1,
    "author":  "Webkul Software Pvt. Ltd.",
    "license":  "Other proprietary",
    "website":  "https://store.webkul.com/",
    "description":  """https://store.webkul.com/""",
    "live_test_url":  "https://store.webkul.com/",
    "depends":  [
        'sms_notification',
    ],
    "data":  [
        'views/msegat_config_view.xml',
        'views/sms_report.xml',
    ],
    "images":  ['static/description/Banner.gif'],
    "application":  True,
    "installable":  True,
    "auto_install":  False,
    "price":  50,
    "currency":  "USD",
    "pre_init_hook":  "pre_init_check",
    "external_dependencies": {
        'python': ['urllib3'],
    },
}
