<template>
	<div>
		<div class="flex justify-end mb-3">
			<Button
				icon-left="download"
				class="shrink-0"
				@click="$resources.downloadInvoiceAsCSV.submit"
			>
				<span class="text-sm">Download as CSV</span>
			</Button>
		</div>
		<div v-if="doc" class="overflow-x-auto">
			<table
				class="text w-full border-separate border-spacing-y-2 text-base font-normal text-gray-900"
			>
				<thead class="bg-gray-100">
					<tr class="text-gray-600">
						<th class="rounded-l p-2 text-left font-normal">Description</th>
						<th class="whitespace-nowrap p-2 text-right font-normal">Rate</th>
						<th class="whitespace-nowrap p-2 text-right font-normal">
							Quantity
						</th>
						<th class="rounded-r p-2 text-right font-normal">Amount</th>
					</tr>
				</thead>
				<tbody>
					<template v-for="(items, type) in groupedLineItems" :key="type">
						<tr class="mt-1 bg-gray-50">
							<td colspan="100" class="rounded p-2 text-base font-medium">
								{{ type }}
							</td>
						</tr>
						<tr v-for="(row, i) in items" :key="row.idx">
							<td class="py-1 pl-2 pr-2">
								{{ row.document_name }}
								<span v-if="row.plan" class="text-gray-700">
									({{ formatPlan(row.plan) }}/mo)
								</span>
							</td>
							<td class="py-1 pl-2 pr-2 text-right">
								{{ formatCurrency(row.rate) }}
							</td>
							<td class="py-1 pl-2 pr-2 text-right">
								{{ row.quantity }}
								{{
									[
										'Site',
										'Release Group',
										'Server',
										'Database Server',
									].includes(row.document_type)
										? $format.plural(row.quantity, 'day', 'days')
										: ''
								}}
							</td>
							<td class="py-1 pl-2 pr-2 text-right font-medium">
								{{ formatCurrency(row.amount) }}
							</td>
						</tr>
					</template>
				</tbody>
				<tfoot>
					<tr v-if="doc.total_discount_amount > 0">
						<td></td>
						<td></td>
						<td class="pb-2 pr-2 pt-4 text-right font-medium">
							Total Without Discount
						</td>
						<td class="whitespace-nowrap pb-2 pr-2 pt-4 text-right font-medium">
							{{ formatCurrency(doc.total_before_discount) }}
						</td>
					</tr>
					<tr v-if="doc.total_discount_amount > 0">
						<td></td>
						<td></td>
						<td class="pb-2 pr-2 pt-4 text-right font-medium">
							Total Discount Amount
						</td>
						<td class="whitespace-nowrap pb-2 pr-2 pt-4 text-right font-medium">
							{{
								$team.doc.erpnext_partner
									? formatCurrency(doc.total_discount_amount)
									: formatCurrency(0)
							}}
						</td>
					</tr>
					<tr v-if="doc.gst > 0">
						<td></td>
						<td></td>
						<td class="pb-2 pr-2 pt-4 text-right font-medium">
							Total (Without Tax)
						</td>
						<td class="whitespace-nowrap pb-2 pr-2 pt-4 text-right font-medium">
							{{ formatCurrency(doc.total) }}
						</td>
					</tr>
					<tr v-if="doc.gst > 0">
						<td></td>
						<td></td>
						<td class="pb-2 pr-2 pt-4 text-right font-medium">
							IGST @ {{ Number(gstPercentage * 100) }}%
						</td>
						<td class="whitespace-nowrap pb-2 pr-2 pt-4 text-right font-medium">
							{{ doc.gst }}
						</td>
					</tr>
					<tr>
						<td></td>
						<td></td>
						<td class="pb-2 pr-2 pt-4 text-right font-medium">Grand Total</td>
						<td class="whitespace-nowrap pb-2 pr-2 pt-4 text-right font-medium">
							{{ formatCurrency(doc.total + doc.gst) }}
						</td>
					</tr>
					<template
						v-if="
							doc.total !== doc.amount_due &&
							['Paid', 'Unpaid'].includes(doc.status)
						"
					>
						<tr>
							<td></td>
							<td></td>
							<td class="pr-2 text-right font-medium">Applied Balance</td>
							<td class="whitespace-nowrap py-3 pr-2 text-right font-medium">
								- {{ formatCurrency(doc.applied_credits) }}
							</td>
						</tr>
						<tr>
							<td></td>
							<td></td>
							<td class="pr-2 text-right font-medium">Amount Due</td>
							<td class="whitespace-nowrap py-3 pr-2 text-right font-medium">
								{{ formatCurrency(doc.amount_due) }}
							</td>
						</tr>
					</template>
				</tfoot>
			</table>
		</div>
		<div class="py-20 text-center" v-if="$resources.invoice.loading">
			<Button :loading="true">Loading</Button>
		</div>
	</div>
</template>
<script>
import { getPlans } from '../data/plans';

export default {
	name: 'InvoiceTable',
	props: ['invoiceId'],
	resources: {
		invoice() {
			return {
				type: 'document',
				doctype: 'Invoice',
				name: this.invoiceId,
			};
		},
		downloadInvoiceAsCSV() {
			return {
				url: 'press.api.billing.fetch_invoice_items',
				makeParams() {
					return {
						invoice: this.invoiceId,
					};
				},
				onSuccess(data) {
					const filename = `${this.invoiceId}.csv`;
					this.downloadAsCSV(data, filename);
				},
			};
		},
	},
	computed: {
		groupedLineItems() {
			if (!this.doc) return {};
			const groupedLineItems = {};
			for (let item of this.doc.items) {
				groupedLineItems[item.document_type] =
					groupedLineItems[item.document_type] || [];
				groupedLineItems[item.document_type].push(item);
			}
			return groupedLineItems;
		},
		doc() {
			return this.$resources.invoice.doc;
		},
		gstPercentage() {
			return this.$team.doc.billing_info.gst_percentage;
		},
	},
	methods: {
		formatPlan(plan) {
			let planDoc = getPlans().find((p) => p.name === plan);
			if (planDoc) {
				let india = this.$team.doc.currency === 'INR';
				return this.$format.userCurrency(
					india ? planDoc.price_inr : planDoc.price_usd,
				);
			}
			return plan;
		},
		formatCurrency(value) {
			if (!this.doc) return;
			let currency = this.doc.currency;
			return this.$format.currency(value, currency);
		},
		downloadAsCSV(data, filename) {
			if (!data || data.length === 0) return;
			let result = [];
			result[0] = Object.keys(data[0]);
			data.forEach((row) => {
				result.push(Object.values(row));
			});
			const csv = result.map((row) => Object.values(row).join(',')).join('\n');
			const blob = new Blob([csv], { type: 'text/csv' });
			const url = window.URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = filename;
			a.click();
			window.URL.revokeObjectURL(url);
		},
	},
};
</script>
