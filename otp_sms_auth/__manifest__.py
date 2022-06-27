# -*- coding: utf-8 -*-
#################################################################################
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
#################################################################################
{
  "name"                 :  "Odoo SMS OTP Authentication",
  "summary"              :  """SMS OTP Authentication""",
  "category"             :  "website",
  "version"              :  "2.0.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-SMS-OTP-Authentication.html",
  "description"          :  """This module works very well with latest version of Odoo 13.0
--------------------------------------------------------------""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=otp_sms_auth",
  "depends"              :  [
                             'sms_notification',
                             'otp_auth',
                            ],
  "data"                 :  [
                             'data/data_smsotp.xml',
                             'views/res_config_views.xml',
                             'views/auth_signup_login_templates.xml',
                             'edi/sms_template_for_otp_sms.xml',
                             'views/res_users_view.xml',
                             'views/webclient_templates.xml',
                            ],
  "assets"               : {
                            'web.assets_frontend':['otp_sms_auth/static/src/js/wk_otp.js',
                                                    'otp_sms_auth/static/src/less/wk_sms_otp.scss'],
                            },
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  45,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}