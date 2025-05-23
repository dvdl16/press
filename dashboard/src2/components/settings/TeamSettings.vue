<template>
	<div class="p-5">
		<ObjectList :options="teamMembersListOptions"> </ObjectList>
	</div>
</template>

<script setup>
import { defineAsyncComponent, h, ref } from 'vue';
import { toast } from 'vue-sonner';
import { getTeam } from '../../data/team';
import { confirmDialog, renderDialog } from '../../utils/components';
import ObjectList from '../ObjectList.vue';
import UserWithAvatarCell from '../UserWithAvatarCell.vue';
import { getToastErrorMessage } from '../../utils/toast';

const team = getTeam();
team.getTeamMembers.submit();
const teamMembersListOptions = ref({
	onRowClick: () => {},
	rowHeight: 50,
	list: team.getTeamMembers,
	columns: [
		{
			label: 'User',
			type: 'Component',
			component: ({ row }) => {
				return h(UserWithAvatarCell, {
					avatarImage: row.user_image,
					fullName: row.full_name,
					email: row.email
				});
			},
			width: 1
		}
	],
	rowActions({ row }) {
		let team = getTeam();
		if (row.name === team.doc.user || row.name === team.doc.user_info?.name)
			return [];
		return [
			{
				label: 'Remove Member',
				condition: () => row.name !== team.doc.user,
				onClick() {
					if (team.removeTeamMember.loading) return;
					confirmDialog({
						title: 'Remove Member',
						message: `Are you sure you want to remove <b>${row.full_name}</b> from the team?`,
						onSuccess({ hide }) {
							if (team.removeTeamMember.loading) return;
							toast.promise(
								team.removeTeamMember.submit({ member: row.name }),
								{
									loading: 'Removing Member...',
									success: () => {
										team.getTeamMembers.submit();
										hide();
										return 'Member Removed';
									},
									error: e => getToastErrorMessage(e)
								}
							);
						}
					});
				}
			}
		];
	},
	actions() {
		return [
			{
				label: 'Settings',
				iconLeft: 'settings',
				onClick() {
					const TeamSettingsDialog = defineAsyncComponent(() =>
						import('./TeamSettingsDialog.vue')
					);
					renderDialog(h(TeamSettingsDialog));
				}
			},
			{
				label: 'Add Member',
				variant: 'solid',
				iconLeft: 'plus',
				onClick() {
					const InviteTeamMemberDialog = defineAsyncComponent(() =>
						import('./InviteTeamMemberDialog.vue')
					);
					renderDialog(h(InviteTeamMemberDialog));
				}
			}
		];
	}
});
</script>
