import flet as ft
import traceback
import asyncio

def main(page: ft.Page):
    # --- 1. PLATFORM DETECTION ---
    is_mobile = page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]

    # --- 2. MOBILE CRASH HANDLERS ---
    if is_mobile:
        try:
            loop = asyncio.get_event_loop()
            def suppress_connection_error(loop, context):
                msg = context.get("message", "")
                if "10054" in str(msg) or isinstance(context.get("exception"), ConnectionResetError):
                    return
                loop.default_exception_handler(context)
            loop.set_exception_handler(suppress_connection_error)
        except: pass

    try:
        from datetime import datetime
        from sidebar import Sidebar
        from top_bar import FactoryHeader
        from settings_view import SettingsView
        from location_view import LocationView, parse_date

        BG_COLOR = "#F8FAFC"
        CARD_BG = "#FFFFFF"
        TEXT_MAIN = "#0F172A"
        TEXT_SUB = "#64748B"
        PRIMARY = "#2563EB"

        page.title = "Amin & Sons ERP"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 0
        page.spacing = 0
        page.bgcolor = BG_COLOR

        # --- 3. TEMPORARY RAM STORAGE ONLY ---
        # ALL storage and permission logic removed to guarantee no white screen crashes.
        products_config = {}
        factories = []
        factory_sub_locations = {}
        level3_data = {}
        
        active_factory_index = 0
        current_nav_index = 0

        def save_db():
            # Does nothing. Data is naturally kept in the app's RAM while it runs.
            # Kept here so your UI components don't throw errors when they try to trigger a save.
            pass

        def show_snack(msg, is_error=False):
            page.open(ft.SnackBar(content=ft.Text(msg, color="#FFFFFF", weight=ft.FontWeight.W_500), bgcolor="#EF4444" if is_error else "#10B981", behavior=ft.SnackBarBehavior.FLOATING, margin=20, shape=ft.RoundedRectangleBorder(radius=8)))

        # --- UI COMPONENTS ---
        text_input = ft.TextField(autofocus=True, border_radius=8, border_color="#CBD5E1", focused_border_color=PRIMARY, cursor_color=PRIMARY)
        dialog_mode = "" 
        target_edit_index = 0 

        def close_dialog(e=None): page.close(main_dialog)

        def process_dialog(e):
            val = text_input.value.strip()
            if not val: show_snack("Name cannot be empty!", True); return
            nonlocal active_factory_index
            current_factory = factories[active_factory_index] if factories else None

            if dialog_mode == "add_factory":
                if val in factories: show_snack("Factory already exists!", True); return
                factories.append(val); factory_sub_locations[val] = []; active_factory_index = len(factories) - 1
                show_snack(f"Factory '{val}' added!")
            elif dialog_mode == "add_loc":
                if val in factory_sub_locations[current_factory]: show_snack("Location already exists!", True); return
                factory_sub_locations[current_factory].append(val); show_snack("Location added!")
            elif dialog_mode == "edit_factory":
                if val != current_factory and val in factories: show_snack("Name already exists!", True); return
                factories[active_factory_index] = val; factory_sub_locations[val] = factory_sub_locations.pop(current_factory); show_snack("Factory updated!")
            elif dialog_mode == "edit_loc":
                old_val = factory_sub_locations[current_factory][target_edit_index]
                if val != old_val and val in factory_sub_locations[current_factory]: show_snack("Name already exists!", True); return
                factory_sub_locations[current_factory][target_edit_index] = val; show_snack("Location updated!")

            close_dialog(); save_db(); refresh_ui()

        main_dialog = ft.AlertDialog(shape=ft.RoundedRectangleBorder(radius=12), title=ft.Text("", weight=ft.FontWeight.BOLD, color=TEXT_MAIN), content=text_input, actions=[ft.TextButton("Cancel", on_click=close_dialog, style=ft.ButtonStyle(color=TEXT_SUB)), ft.ElevatedButton("Save", on_click=process_dialog, bgcolor=PRIMARY, color="#FFFFFF", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))])
        def open_dialog(mode, title, default_val=""): nonlocal dialog_mode; dialog_mode = mode; main_dialog.title.value = title; text_input.value = default_val; page.open(main_dialog)

        def delete_active_factory(e):
            nonlocal active_factory_index, current_nav_index
            factory_to_delete = factories[active_factory_index]
            factories.pop(active_factory_index); del factory_sub_locations[factory_to_delete]
            active_factory_index = 0; current_nav_index = 0
            show_snack("Factory deleted!"); save_db(); refresh_ui()

        def edit_sidebar_loc(index): nonlocal target_edit_index; target_edit_index = index - 2; open_dialog("edit_loc", "Edit Location", factory_sub_locations[factories[active_factory_index]][target_edit_index])
        def delete_sidebar_loc(index):
            nonlocal current_nav_index; sub_loc_index = index - 2; factory_sub_locations[factories[active_factory_index]].pop(sub_loc_index)
            if current_nav_index == index: current_nav_index = 0 
            show_snack("Location deleted!"); save_db(); refresh_ui()

        def get_current_l3_context(): return factories[active_factory_index], factory_sub_locations[factories[active_factory_index]][current_nav_index - 2]
        
        location_view = LocationView(page, products_config, get_current_l3_context, factories, factory_sub_locations, level3_data, save_db)
        
        # --- SAFE OVERLAY LOADING ---
        if hasattr(location_view, 'overlay_controls'):
            for ctrl in location_view.overlay_controls:
                page.overlay.append(ctrl)

        settings_view = SettingsView(page, products_config, save_db)

        dash_title = ft.Text("Global Overview", size=24, weight=ft.FontWeight.W_800, color=TEXT_MAIN)
        dash_start_date = datetime.now()
        dash_end_date = datetime.now()
        dash_list = ft.ListView(expand=True, spacing=15, padding=ft.padding.only(bottom=40))
        
        def on_dash_start_change(e): nonlocal dash_start_date; dash_start_date = dash_start_picker.value; refresh_ui()
        def on_dash_end_change(e): nonlocal dash_end_date; dash_end_date = dash_end_picker.value; refresh_ui()
        def clear_dash_dates(e): nonlocal dash_start_date, dash_end_date; dash_start_date = None; dash_end_date = None; refresh_ui()
            
        dash_start_picker = ft.DatePicker(on_change=on_dash_start_change)
        dash_end_picker = ft.DatePicker(on_change=on_dash_end_change)
        
        page.overlay.append(dash_start_picker)
        page.overlay.append(dash_end_picker)

        dashboard_overview = ft.Container(padding=ft.padding.all(15), visible=True, expand=True, content=ft.Column(expand=True, controls=[
            ft.Row([dash_title], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Container(height=5),
            ft.Container(padding=15, bgcolor=CARD_BG, border_radius=12, border=ft.border.all(1, "#E2E8F0"), shadow=ft.BoxShadow(blur_radius=15, color="#0000000A", offset=ft.Offset(0, 4)), content=ft.Row([
                ft.Row([ft.Icon(ft.Icons.FILTER_ALT, color=TEXT_SUB, size=20), ft.Text("Activity Date Filter:", color=TEXT_SUB, weight=ft.FontWeight.W_500)]),
                ft.Row([
                    ft.ElevatedButton(f"Start: {dash_start_date.strftime('%d %b %Y') if dash_start_date else 'Any'}", on_click=lambda _: dash_start_picker.pick_date(), icon=ft.Icons.CALENDAR_TODAY, color=TEXT_MAIN, bgcolor="#F1F5F9", elevation=0, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))),
                    ft.ElevatedButton(f"End: {dash_end_date.strftime('%d %b %Y') if dash_end_date else 'Any'}", on_click=lambda _: dash_end_picker.pick_date(), icon=ft.Icons.CALENDAR_TODAY, color=TEXT_MAIN, bgcolor="#F1F5F9", elevation=0, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))),
                    ft.IconButton(ft.Icons.CLOSE, on_click=clear_dash_dates, tooltip="Clear Dates", icon_color="#EF4444", bgcolor="#FEF2F2")
                ], wrap=True) 
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True)), 
            ft.Container(height=10), dash_list
        ]))

        def toggle_sidebar(show: bool):
            if show:
                sidebar.left = 0
                sidebar_overlay.visible = True
            else:
                sidebar.left = -280
                sidebar_overlay.visible = False
            page.update()

        def on_top_tab_change(index): 
            nonlocal active_factory_index, current_nav_index
            active_factory_index = index; current_nav_index = 0
            settings_view.expanded_products.clear(); location_view.expanded_active_groups.clear(); location_view.expanded_history_groups.clear()
            refresh_ui()

        def on_nav_change(index):
            nonlocal current_nav_index
            if not factories: show_snack("Add a factory first!", True); return
            current_nav_index = index
            settings_view.expanded_products.clear(); location_view.expanded_active_groups.clear(); location_view.expanded_history_groups.clear()
            if page.width and page.width < 768: toggle_sidebar(False)
            refresh_ui()

        header = FactoryHeader(on_tab_change=on_top_tab_change, on_add_click=lambda e: open_dialog("add_factory", "Add New Factory"), on_edit_click=lambda e: open_dialog("edit_factory", "Edit Factory", factories[active_factory_index]), on_delete_click=delete_active_factory, on_menu_click=lambda e: toggle_sidebar(True))
        sidebar = Sidebar(on_nav_change=on_nav_change, on_add_click=lambda: open_dialog("add_loc", "Add Sidebar Location") if factories else show_snack("Add a factory first!", True), on_edit_click=edit_sidebar_loc, on_delete_click=delete_sidebar_loc)
        
        sidebar.left = 0
        sidebar.top = 0
        sidebar.bottom = 0
        
        content_area = ft.Container(
            margin=ft.margin.only(left=260), 
            expand=True,
            content=ft.Column(expand=True, spacing=0, controls=[header, ft.Container(expand=True, content=ft.Stack([dashboard_overview, settings_view, location_view]))])
        )

        sidebar_overlay = ft.Container(bgcolor="#80000000", expand=True, visible=False, on_click=lambda e: toggle_sidebar(False))
        root_stack = ft.Stack(controls=[content_area, sidebar_overlay, sidebar], expand=True)

        def page_resize(e):
            pw = page.width
            if pw is None: pw = 400 
            if pw < 768:
                content_area.margin = ft.margin.all(0)
                header.set_menu_visible(True)
                if not sidebar_overlay.visible: sidebar.left = -280 
            else:
                content_area.margin = ft.margin.only(left=260)
                header.set_menu_visible(False)
                sidebar.left = 0
                sidebar_overlay.visible = False
            page.update()

        page.on_resized = page_resize

        def populate_dashboard():
            dash_list.controls.clear()
            dashboard_items = []
            for key, loc_data in location_view.level3_data.items():
                fac, loc = key.split("::")
                for sub_name, tab_data in loc_data["data"].items():
                    for status_type, item_list in [("active", tab_data.get("active", [])), ("completed", tab_data.get("history", []))]:
                        for item in item_list:
                            if status_type == "completed" and item.get("entry_type") != "Batch": continue
                            valid_logs = []
                            for log in item["timeline"]:
                                log_time = parse_date(log["time"])
                                if dash_start_date and log_time.date() < dash_start_date.date(): continue
                                if dash_end_date and log_time.date() > dash_end_date.date(): continue
                                valid_logs.append(log)
                            if not valid_logs: continue 
                            valid_logs.reverse()
                            latest_time = parse_date(valid_logs[0]["time"])
                            dashboard_items.append({"item": item, "fac": fac, "loc": loc, "sub_name": sub_name, "status_type": status_type, "valid_logs": valid_logs, "latest_time": latest_time})
            dashboard_items.sort(key=lambda x: x["latest_time"], reverse=True)
            if not dashboard_items:
                dash_list.controls.append(ft.Container(padding=40, alignment=ft.alignment.center, content=ft.Text("No active or completed processes found in this date range.", color=TEXT_SUB, size=16)))
                return
            for d_item in dashboard_items:
                item = d_item["item"]; status_type = d_item["status_type"]; valid_logs = d_item["valid_logs"]
                loc_label = "Current" if status_type == "active" else "Final"
                timeline_controls = []
                for i, log in enumerate(valid_logs):
                    color = TEXT_MAIN if i == 0 else TEXT_SUB; weight = ft.FontWeight.W_500 if i == 0 else ft.FontWeight.NORMAL
                    dt_obj = parse_date(log['time'])
                    time_formatted = dt_obj.strftime("%d %b %Y, %I:%M %p")
                    timeline_controls.append(ft.Row([ft.Icon(ft.Icons.CIRCLE, size=8, color="#CBD5E1"), ft.Text(f"{log['step']}", size=13, color=color, weight=weight, expand=True), ft.Text(time_formatted, size=11, color="#94A3B8")]))
                subtitle_col = ft.Column([ft.Container(height=5), ft.Row([ft.Icon(ft.Icons.LOCATION_ON, size=14, color="#94A3B8"), ft.Text(f"{loc_label}: {d_item['fac']} → {d_item['loc']} → {d_item['sub_name']}", size=13, color=TEXT_SUB, weight=ft.FontWeight.W_500, expand=True)]), ft.Container(padding=ft.padding.only(left=5, top=5), content=ft.Column(timeline_controls, spacing=4))], spacing=0)

                if status_type == "active":
                    icon_color = PRIMARY; title_text = f"{item['type']} - {item['name']}"; step_val = f"Step {item['step_idx']}/{len(item['steps'])}"
                    chip_bg = "#FEF3C7" if item.get("is_processing") else "#DBEAFE"; chip_color = "#D97706" if item.get("is_processing") else PRIMARY; chip_text = "In Process" if item.get("is_processing") else "Pending"
                else:
                    icon_color = "#10B981"; title_text = f"{item['type']} - {item['name']}"; step_val = "100%"; chip_bg = "#D1FAE5"; chip_color = "#059669"; chip_text = "Completed"

                status_chip = ft.Container(padding=ft.padding.symmetric(horizontal=10, vertical=4), bgcolor=chip_bg, border_radius=16, content=ft.Text(chip_text, size=11, color=chip_color, weight=ft.FontWeight.BOLD))
                dash_card = ft.Container(bgcolor=CARD_BG, border_radius=12, padding=15, border=ft.border.all(1, "#E2E8F0"), shadow=ft.BoxShadow(blur_radius=10, color="#00000008", offset=ft.Offset(0, 4)), content=ft.Row([
                    ft.Container(padding=12, bgcolor="#F8FAFC", border_radius=12, content=ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, color=icon_color, size=24)),
                    ft.Column([ft.Row([ft.Text(title_text, size=15, weight=ft.FontWeight.BOLD, color=TEXT_MAIN, expand=True), status_chip], spacing=5), subtitle_col], expand=True),
                ], vertical_alignment=ft.CrossAxisAlignment.START))
                dash_list.controls.append(dash_card)

        def refresh_ui():
            if not factories:
                header.update_tabs([], 0); sidebar.update_locations([], 0); dashboard_overview.visible = True; settings_view.visible = False; location_view.visible = False; page.update(); return

            current_factory = factories[active_factory_index]
            header.update_tabs(factories, active_factory_index); sidebar.update_locations(factory_sub_locations[current_factory], current_nav_index)
            dashboard_overview.visible = False; settings_view.visible = False; location_view.visible = False

            if current_nav_index == 0: populate_dashboard(); dashboard_overview.visible = True
            elif current_nav_index == 1: settings_view.visible = True
            else: location_view.update_context(); location_view.visible = True
            page.update()

        page.add(root_stack)
        page_resize(None) 
        refresh_ui()

    except Exception as e:
        error_msg = traceback.format_exc()
        try: page.clean()
        except: pass
        page.add(ft.SafeArea(ft.Column([
            ft.Text("APP CRASHED!", color=ft.colors.RED_700, weight="bold", size=22),
            ft.Text(f"Error: {str(e)}", color=ft.colors.BLACK, size=14, weight="bold"),
            ft.Container(padding=10, bgcolor=ft.colors.GREY_200, border_radius=8, expand=True, content=ft.Text(error_msg, color=ft.colors.BLACK, size=11, selectable=True))
        ], scroll=ft.ScrollMode.AUTO, expand=True)))
        page.update()

ft.app(target=main)