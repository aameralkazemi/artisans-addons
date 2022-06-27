/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
odoo.define('otp_auth.wk_otp_login', function (require) {
    "use strict";
    
    var ajax = require('web.ajax');
    $(document).ready(function() {
        // if ($('#mobile')) {
        //     $("#login").val('');
        // }
        $("#login").keyup(function(event) {
            if (event.keyCode === 13) {
                $(".wk_next_btn").click();
            }
        });
        $("#mobile").keyup(function(event) {
            if (event.keyCode === 13) {
                $(".wk_next_btn").click();
            }
        });
        $('.wk_next_btn').on('click', function(e) {

            var logintype = $('input[name=radio-login]:checked').val();
            if (logintype == 'radiomobile') {
                $("#login").prop('required',false);
                $("#login").val('');
                // $("#mobile").val('');
                // $("#login").prop('required',true);
            }
            $('#wk_error').remove();
            if ($(".field-otp-option").css("display") == 'none') {
                $(".field-login").hide();
                $(".wk_back_btn").show();
                $(".field-otp-option").css("display","");
            } else {
                var radioVal = $('input[name=radio-otp]:checked').val();
                if (radioVal == 'radiotp') {
                    generateLoginOtp();
                } else if (radioVal == 'radiopwd') {
                    $(".field-password").removeClass('d-none');
                    $(".field-password").addClass('d-block');
                    $("#password").attr('placeholder', 'Enter Password');
                    $(":submit").removeClass('d-none');
                    $(":submit").addClass('d-block');
                    $(".wk_next_btn").hide();
                    $(".field-otp-option").css("display","none");
                }
            }
        });

        $('input:radio[name="radio-otp"]').change(function() {
            if ($(this).val() == 'radiotp') {
                $('label[for=password], input#password').text("OTP");
            } else if ($(this).val() == 'radiopwd') {
                $('label[for=password], input#password').text("Password");
            }
        });

        $(this).on('click', '.wk_login_resend', function(e) {
            generateLoginOtp();
        });
        $('label[for="password"]').show();
    });

    function generateLoginOtp() {
        var mobile = $('#mobile').val();
        var email = $('#login').val();
        var otp_type = $('.otp_type').val();
        var logintype = $('input[name=radio-login]:checked').val();
        $(".field-password>label").text('Enter Otp');
        $("#password").attr('placeholder', 'Enter OTP');
        $("div#wk_loader").addClass('show');
       
            ajax.jsonRpc("/send/otp", 'call', {'email':email, "loginOTP":'loginOTP', 'mobile':mobile, 'logintype':logintype})
            .then(function (data) {
                    if (data) {
                        if (data.email) {
                            if (data.email.status == 1) {
                                hideandshowdata(otp_type, data.email.otp_time);
                                $(".field-password>label").text('Enter Otp');
                                $(".field-password").after("<p id='wk_error' class='alert alert-success'>" +data.email.message + "</p>");
                                $(":submit").removeAttr("disabled")
                            } else {
                                $("div#wk_loader").removeClass('show');
                                $('#wk_error').remove();
                                $(".field-otp-option").after("<p id='wk_error' class='alert alert-danger'>" +data.email.message + "</p>");
                            }
                        }
                        if (data.mobile) {
                            if (data.mobile.status == 1) {
                                if (data.email) {
                                    if (data.email.status != 1) {
                                        hideandshowdata(otp_type, data.email.otp_time);
                                    }
                                }
                                $(".field-password").after("<p id='wk_error' class='alert alert-success'>" +data.mobile.message + "</p>");
                            } 
                            else {
                                if (data.email) {
                                    if (data.email.status != 1) {
                                        $("div#wk_loader").removeClass('show');
                                        $('#wk_error').remove();
                                    }
                                }
                                $(".field-otp-option").after("<p id='wk_error' class='alert alert-danger'>" +data.mobile.message + "</p>");
                            }
                        }
                    }
                });
        // }
    }

    function hideandshowdata(otp_type, otp_time) {
        getLoginInterval(otp_time);
        $("div#wk_loader").removeClass('show');
        $('#wk_error').remove();
        $(".field-password").removeClass('d-none');
        $(".field-password").addClass('d-block');
        $("#password").attr('placeholder', 'Enter OTP');
        if (otp_type == '4') {
            $("#password").attr("type", "text");
        }
        $(":submit").removeClass('d-none');
        $(":submit").addClass('d-block');
        $(".wk_next_btn").hide();
        $(".field-otp-option").css("display","none");
    }

    function getLoginInterval(otpTimeLimit) {
        var countDown = otpTimeLimit;
        var x = setInterval(function() {
            countDown = countDown - 1;
            $("#otplogincounter").html("OTP will expire in " + countDown + " seconds.");
            if (countDown < 0) {
                clearInterval(x);
                $('#wk_error').remove();
                $('#wk_error').remove();
                $("#otplogincounter").html("<a class='btn btn-link pull-right wk_login_resend' href='#'>Resend OTP</a>");
                $(":submit").attr("disabled", true);
            }
        }, 1000);
    }

})
