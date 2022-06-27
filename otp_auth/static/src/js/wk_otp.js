/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
odoo.define('otp_auth.wk_otp', function (require) {
    "use strict";
    
    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;

    $(document).ready(function() {
        var ValidUser = 0;
        if ($('#otpcounter').get(0)) {
            $(":submit").attr("disabled", true);
        }
        
        $('.wk_send').on('click', function(e) {
            if($(this).closest('form').hasClass('oe_reset_password_form')){
                ValidUser = 1;
            }
            var email = $('#login').val();
            if (email) {
                if(validateEmail(email)) {
                    if (validateOtherFields()) {
                        generateOtp(ValidUser);   
                    }
                } else {
                    $('#wk_error').remove();
                    $(".field-confirm_password").after("<p id='wk_error' class='alert alert-danger'>Please enter valid email address.</p>");
                }
            } else {
                $('#wk_error').remove();
                $(".field-confirm_password").after("<p id='wk_error' class='alert alert-danger'>Please enter valid email address.</p>");
            }
        });
        $(this).on('click', '.wk_resend', function(e) {
            $(".wkcheck").remove();
            generateOtp(ValidUser);
        });
        verifyOtp();
    });

    function validateEmail(emailId) {
        var mailRegex = /^([\w-\.]+)@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|(([\w-]+\.)+))([a-zA-Z]{2,4}|[0-9]{1,3})(\]?)$/;
        return mailRegex.test(emailId);
    };

    function validateOtherFields() {
        var username = $('#name').val();
        var errormsg = '';
        if (!username) {
            errormsg = "<p id='wk_error' class='alert alert-danger'>Please enter valid name.</p>";
        } 
        else {      
            var password = $('#password').val();
            if (!password) {
                errormsg = "<p id='wk_error' class='alert alert-danger'>Please enter the valid password.</p>";
            } else {
                var confirm_password = $('#confirm_password').val();
                if (!confirm_password) {
                    errormsg = "<p id='wk_error' class='alert alert-danger'>Please enter the valid confirm password.</p>";
                } else {
                    if (confirm_password != password) {
                        errormsg = "<p id='wk_error' class='alert alert-danger'>Passwords do not match; please retype them</p>";
                    } else {
                        return true;
                    }
                }
            }
            
        }
        if (errormsg) {
            $('#wk_error').remove();
            $(".field-confirm_password").after(errormsg);
        }
    }

    function getInterval(otpTimeLimit) {
        var countDown = otpTimeLimit;
        $("#wkotp").show();
        var x = setInterval(function() {
            countDown = countDown - 1;
            $("#otpcounter").html("OTP will expire in " + countDown + " seconds.");            
            if (countDown < 0) {
                clearInterval(x);
                $("#otpcounter").html("<a class='btn btn-link pull-right wk_resend position-relative' href='#'>Resend OTP</a>");
                $("#otpcounter").append('<span>Otp is expire.Please Click on resend button</span>');
                $(":submit").attr("disabled", true);
            }
        }, 1000);
    }

    function generateOtp(ValidUser) {
        var email = $('#login').val();
        var mobile = $('#mobile').val();
        var userName = $('#name').val();
        var country_id = $('#country_id').val();
        $("div#wk_loader").addClass('show');
        $('#wk_error').remove();
        $('.alert.alert-danger').remove();
        
        ajax.jsonRpc("/generate/otp", 'call', {'email':email, 'userName':userName, 'mobile':mobile, 'country':country_id,'validUser':ValidUser})
            .then(function (data) {
                if (data[0] == 1) {
                    $("div#wk_loader").removeClass('show');
                    $('.wk_send').remove();
                    getInterval(data[2]);
                    $("#wkotp").after("<p id='wk_error' class='alert alert-success'>" +data[1] + "</p>");
                    $("#otp").css("display","");
                    $('#otp').after($('#otpcounter'));
                } else {
                    $("div#wk_loader").removeClass('show');
                    $('#wk_error').remove();
                    $(".field-confirm_password").after("<p id='wk_error' class='alert alert-danger'>" +data[1] + "</p>");
                }
            });
    }

    function verifyOtp() {
        $('#otp').bind('input propertychange', function() {
            if ($(this).val().length == 6) {
                var otp = $(this).val();
                ajax.jsonRpc("/verify/otp", 'call', {'otp':otp})
                    .then(function (data) {
                        if (data) {
                            $('#otp').after("<i class='fa fa-check-circle wkcheck' aria-hidden='true'></i>");
                            $(".wkcheck").css("color","#3c763d");
                            $('#wkotp').removeClass("form-group has-error");
                            $('#wkotp').addClass("form-group has-success");
                            $(":submit").removeAttr("disabled").find('.fa-refresh').addClass('d-none');
                        } else {
                            $(":submit").attr("disabled", true);
                            $('#otp').after("<i class='fa fa-times-circle wkcheck' aria-hidden='true'></i>");
                            $('#wkotp').removeClass("form-group has-success");
                            $(".wkcheck").css("color","#a94442");
                            $('#wkotp').addClass("form-group has-error");
                        }
                    });
            } else {
                $(":submit").attr("disabled", true);
                $(".wkcheck").remove();
                $('#wkotp').removeClass("form-group has-success");
                $('#wkotp').removeClass("form-group has-error");
                $('#wkotp').addClass("form-group");
            }
        });
    }

})
