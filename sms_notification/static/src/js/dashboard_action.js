odoo.define('sms_notification.dashboard',function (require) {
	'use strict'

	var AbstractAction = require('web.AbstractAction')
	var ajax = require('web.ajax')
	var core = require('web.core')
    var _t = require('web.core')._t;

    var D3_COLORS = ["#1f77b4","#ff7f0e","#aec7e8","#ffbb78","#2ca02c","#98df8a","#d62728", "#ff9896","#9467bd","#c5b0d5","#8c564b","#c49c94","#e377c2","#f7b6d2", "#7f7f7f","#c7c7c7","#bcbd22","#dbdb8d","#17becf","#9edae5"];

	var SMSNotificationDashboard = AbstractAction.extend({
		template: 'dashboard_template',
		jsLibs: [
			'/web/static/lib/Chart/Chart.js',
		],
		events: {
			'click ._action': 'on_action',
			'change #line_date_change': 'reload_line_graph',
			'change #line_obj_change': 'reload_line_graph',
			'change #pie_obj_change': 'reload_pie_graph',
		},

		willStart () {
			var self = this
			return $.when(
				ajax.loadLibs(this),
				this._super(),
			).then(function () {
				return self.fetch_data()
			})
		},

		on_attach_callback () {
			this.render_line_graph()
			this.render_pie_graph()
		},

		reload_line_graph () {
			var self = this
			var selected_option = $('#line_obj_change option:selected').val()
			var line_chart_label = $('#line_chart_label')
			switch (selected_option) {
				case 'new':
					line_chart_label.text('New')
					break
				case 'sent':
					line_chart_label.text('Sent')
					break
				case 'delivered':
					line_chart_label.text('Delivered')
					break
				case 'undelivered':
					line_chart_label.text('Undelivered')
					break
                case 'failed':
					line_chart_label.text('Failed')
					break
				default:
					line_chart_label.text('')
			}
			$.when(
				self.fetch_data(
					selected_option,
					parseInt($('#pie_obj_change option:selected').val()),
					parseInt($('#line_date_change option:selected').val()),
				)
			).then(function () {
				return self.render_line_graph()
			})
		},

		reload_pie_graph () {
			var selected_stage = $('#pie_obj_change option:selected').val()
			var pie_chart_label = $('#pie_chart_label')
			switch (selected_stage) {
				case selected_stage:
					pie_chart_label.text(selected_stage.substr(0,1).toUpperCase()+selected_stage.substr(1))
					break
				default:
					pie_chart_label.text('')
			}
			this.render_pie_graph(selected_stage)
		},

		fetch_data (line_stage='all',pie_stage='total', days=7) {
			var self = this
			return this._rpc({
				route: '/sms_notification/dashboard_data',
				params: {line_stage,pie_stage, days},
			}).then(function (result) {
				self.line_data = result.line_data
				self.gateway_data = result.gateway_data
                self.image = result.image
                self.total_count = result.total_count
                self.sent_count = result.sent_count
                self.delivered_count = result.delivered_count
                self.undelivered_count = result.undelivered_count
                self.failed_count = result.failed_count
				self.connected_count = result.connected_count
			})
		},

		render_line_graph () {
			$('#line_chart').replaceWith($('<canvas/>',{id: 'line_chart'}))
			var self = this
			self.line_chart = new Chart('line_chart',{
				type: 'line',
				data: {
					labels: self.line_data.labels,
					datasets: self.line_data.data.map(i => ({
                        backgroundColor: D3_COLORS[1],
                        borderColor: D3_COLORS[0],
						data: i.count,
						label: i.state,
						fill: false,
					})),
				},
				beginAtZero: false,
				options: {
					maintainAspectfirefoxRatio: false,
					legend: {
						display: false,
					},
					scales: {
						xAxes: [{
							gridLines: {
								display: false,
							},
						}],
						yAxes: [{
							gridLines: {
								display: false,
							},
							ticks: {
								precision: 0,
							},
						}],
					},
				},
			})
		},

		render_pie_graph (obj='total') {
			$('#pie_chart').replaceWith($('<canvas/>',{id: 'pie_chart'}))
			var self = this;
			self.pie_chart = new Chart('pie_chart',{
				type: 'pie',
				data: {
                    labels: Object.keys(self.gateway_data),
                    datasets: [{
                        backgroundColor: Object.values(self.gateway_data).map(function (val, index) {
                            return D3_COLORS[index % 20];
                        }),
                        data: Object.values(self.gateway_data).map(i => i[obj+'_count']),
                    }],
				},
				options: {
					maintainAspectRatio: false,
					cutoutPercentage: 75,
					legend: {
						position: 'bottom',
						labels: {
							usePointStyle: true,
						},
						onClick: explodePie,
					},
				},
			})
			var lastindex;
			function explodePie (e, legendItem, legend) {
				const index = legendItem.index;
				var i, ilen, total;
				for (i = 0, ilen = (self.pie_chart.chart.data.datasets || []).length; i < ilen; ++i) {
			        var meta = self.pie_chart.chart.getDatasetMeta(i);
					total = meta.total;
			        // toggle visibility of index if exists
					meta.data.forEach((m) => {
						if(lastindex && lastindex.index == index){
							if (m._index != lastindex.index) {
								m.hidden = !m.hidden;
							}
							else{
								m.hidden = false;
							}
						}
						else if(legendItem.hidden == true){
							if (m._index == index) {
								m.hidden = false;
							}
							else{
								m.hidden = true;
							}
						}
					});
    			}
				lastindex = legendItem;
				self.pie_chart.chart.update();
				render_pie(meta.total);
			}

			function render_pie (total) {
				var ctx = self.pie_chart.chart.ctx,
				cw = self.pie_chart.chart.width,
				ch = self.pie_chart.chart.height;
                Chart.pluginService.register({
                  beforeDraw: function(chart) {
                    ctx.textBaseline = "top";
                    var fontFamily = 'Poppins';
                    ctx.font = '56px ' + fontFamily;
                    ctx.textAlign ='center' ;
                    ctx.fillStyle = '#ffffff';
                    ctx.clearRect(0, 0, cw, ch);
                    ctx.fillStyle = '#000000';
                    ctx.fillText(total, cw/2, (ch/5));
                    ctx.font = '26px ' + fontFamily;
                    ctx.fillStyle = '#7B8EB7';
                    ctx.fillText('Total SMS', cw/2, (ch/2.5));
                    ctx.save();
                  }
                });
			}
			var vals = Object.values(self.gateway_data).map(i => i[obj+'_count']);
			var total = 0;
			for (var i in vals) {
				total += vals[i];
			}
            render_pie(total);
		},

        on_action (e) {
			e.preventDefault()
			var target = $(e.currentTarget)
			var action = target.data('action');

			switch (action) {
				case 'send_sms':
					return this.do_action({
						name: 'Send SMS',
						type: 'ir.actions.act_window',
						res_model: 'wk.sms.sms',
						views: [[false,'form']],
						target: 'new'
					})
				case 'configuration':
					return this.do_action({
						name: 'Gateway Configuration',
						type: 'ir.actions.act_window',
						res_model: 'sms.mail.server',
						views: [[false,'form']],
						target: 'new'
					})
			}
		},

	})

	core.action_registry.add('sms_notification.dashboard',SMSNotificationDashboard)
})
