import type { defineAsyncComponent, h, Component } from 'vue';
import type { icon } from '../../utils/components';

type ListResource = {
	reload: () => void;
};
export interface Resource {
	name: string;
	doc: Record<string, any>;
	[key: string]: any;
}

type Icon = ReturnType<typeof icon>;
type AsyncComponent = ReturnType<typeof defineAsyncComponent>;

export interface DashboardObject {
	doctype: string;
	whitelistedMethods: Record<string, string>;
	list: List;
	detail: Detail;
	routes: RouteDetail[];
}

export interface Detail {
	titleField: string;
	statusBadge: StatusBadge;
	breadcrumbs: Breadcrumbs;
	route: string;
	tabs: Tab[];
	actions: (r: { documentResource: Resource }) => Action[];
}

export interface List {
	route: string;
	title: string;
	fields: string[]; // TODO: Incomplete
	searchField: string;
	columns: ColumnField[];
	orderBy: string;
	filterControls: FilterControls;
	primaryAction?: PrimaryAction;
}

type FilterControls = () => FilterField[];
type PrimaryAction = (r: { listResource: ListResource }) => {
	label: string;
	variant: string;
	slots: {
		prefix: Icon;
	};
	onClick: () => void;
};
type StatusBadge = (r: { documentResource: Resource }) => { label: string };
export type Breadcrumb = { label: string; route: string };
export type BreadcrumbArgs = {
	documentResource: Resource;
	items: Breadcrumb[];
};
export type Breadcrumbs = (r: BreadcrumbArgs) => Breadcrumb[];

export interface FilterField {
	label: string;
	fieldname: string;
	type: string;
	options?:
		| {
				doctype: string;
				filters?: {
					doctype_name?: string;
				};
		  }
		| string[];
}

export interface ColumnField {
	label: string;
	fieldname?: string;
	class?: string;
	width?: string | number;
	type?: string;
	format?: (value: any, row: Row) => string | undefined;
	link?: (value: unknown, row: Row) => string;
	prefix?: (row: Row) => Component | undefined;
	suffix?: (row: Row) => Component | undefined;
	theme?: (value: unknown) => string;
	align?: 'left' | 'right';
}

export type Row = Record<string, any>;

export interface Tab {
	label: string;
	icon: Icon;
	route: string;
	type: string;
	childrenRoutes?: string[];
	component?: AsyncComponent;
	props?: (r: Resource) => Record<string, unknown>;
	list?: TabList;
}

export interface TabList {
	doctype?: string;
	orderBy?: string;
	filters?: (r: Resource) => Record<string, unknown>;
	route?: (row: Row) => Route;
	pageLength?: number;
	columns: ColumnField[];
	fields?: Record<string, string[]>[] | string[];
	rowActions?: (r: {
		row: Row;
		listResource: ListResource;
		documentResource: Resource;
	}) => Action[];
	primaryAction?: (r: {
		listResource: ListResource;
		documentResource: Resource;
	}) => {
		label: string;
		slots: {
			prefix: Icon;
		};
		onClick: () => void;
		variant?: string;
	};
	filterControls?: () => FilterField[];
	banner?: (r: { documentResource: Resource }) => BannerConfig | undefined;
	searchField?: string;
	experimental?: boolean;
	documentation?: string;
	resource?: (r: { documentResource: Resource }) => {
		url: string;
		params: Record<string, unknown>;
		auto: boolean;
		cache: string[];
	};
}

interface Action {
	label: string;
	slots?: {
		prefix?: Icon;
	};
	theme?: string;
	variant?: string;
	onClick: () => void;
	condition?: () => boolean;
	route?: Route;
	options?: Option[];
}

interface Route {
	name: string;
	params: Record<string, unknown>;
}

export interface RouteDetail {
	name: string;
	path: string;
	component: Component;
}

interface Option {
	label: string;
	icon: Icon | AsyncComponent;
	condition: () => boolean;
	onClick: () => void;
}

export interface BannerConfig {
	title: string;
	dismissable: boolean;
	id: string;
	button?: {
		label: string;
		variant: string;
		onClick?: () => void;
	};
}

export interface DialogConfig {
	title: string;
	message: string;
	primaryAction?: { onClick: () => void };
	onSuccess?: (o: { hide: () => void }) => void;
}

export interface Process {
	program: string;
	name: string;
	status: string;
	uptime?: number;
	uptime_string?: string;
	message?: string;
	group?: string;
	pid?: number;
}
