import flet as ft
import uuid
import copy
from datetime import datetime

CARD_BG = "#FFFFFF"
TEXT_MAIN = "#0F172A"
TEXT_SUB = "#64748B"
PRIMARY = "#2563EB"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
BORDER = "#E2E8F0"

def parse_qty(val):
    try: return float(val)
    except (ValueError, TypeError): return None

def parse_date(date_str):
    try: return datetime.strptime(date_str, "%Y-%m-%d %I:%M %p")
    except ValueError:
        try: return datetime.strptime(date_str, "%I:%M %p, %d %b")
        except: return datetime.now() 

class LocationView(ft.Container):
    def __init__(self, page: ft.Page, products_config: dict, get_context_cb, factories: list, factory_sub_locations: dict, level3_data: dict, save_cb):
        super().__init__()
        self.page = page
        self.products_config = products_config
        self.get_context = get_context_cb 
        self.factories = factories
        self.factory_sub_locations = factory_sub_locations
        
        self.level3_data = level3_data 
        self.save_cb = save_cb 
        
        self.expand = True
        self.padding = 15 
        self.visible = False

        self.current_action_item = None 
        self.current_process_product = None 
        self.is_finishing_batch = False
        
        self.expanded_active_groups = set()
        self.expanded_history_groups = set()

        self.history_start_date = None
        self.history_end_date = None
        self.start_date_picker = ft.DatePicker(on_change=self.on_start_date_change)
        self.end_date_picker = ft.DatePicker(on_change=self.on_end_date_change)
        
        # --- SAFE OVERLAY FIX ---
        # DO NOT APPEND HERE. Main.py will append these safely.
        self.overlay_controls = [self.start_date_picker, self.end_date_picker]

        self.l3_tabs = ft.Tabs(selected_index=0, on_change=self.on_l3_tab_change, animation_duration=300, expand=True, label_color=PRIMARY, unselected_label_color=TEXT_SUB, indicator_color=PRIMARY)
        self.add_l3_btn = ft.IconButton(icon=ft.Icons.ADD_BOX, icon_color=PRIMARY, on_click=self.open_add_l3_dialog)
        
        btn_style = ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        self.add_stock_btn = ft.ElevatedButton("Import Stock", icon=ft.Icons.ADD_SHOPPING_CART, on_click=self.open_add_stock_dialog, bgcolor=TEXT_MAIN, color="#FFFFFF", style=btn_style)
        
        self.view_mode_tabs = ft.Tabs(selected_index=0, on_change=self.on_view_mode_change, animation_duration=300, label_color=PRIMARY, unselected_label_color=TEXT_SUB, indicator_color=PRIMARY)
        self.list_container = ft.ListView(spacing=20, expand=True, padding=ft.padding.only(bottom=40))

        self.content = ft.Column([
            ft.Container(padding=10, bgcolor=CARD_BG, border_radius=12, border=ft.border.all(1, BORDER), shadow=ft.BoxShadow(blur_radius=8, color="#00000005", offset=ft.Offset(0, 2)), content=ft.Row([self.l3_tabs, self.add_l3_btn], alignment=ft.MainAxisAlignment.START)),
            ft.Container(height=10), ft.Row([self.view_mode_tabs, self.add_stock_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True), ft.Container(height=5), self.list_container
        ], expand=True)

        dlg_shape = ft.RoundedRectangleBorder(radius=12)
        self.l3_name_input = ft.TextField(label="Sub-Location Name", autofocus=True, border_radius=8, focused_border_color=PRIMARY)
        self.l3_dialog = ft.AlertDialog(shape=dlg_shape, title=ft.Text("New Sub-Location", weight=ft.FontWeight.BOLD), content=self.l3_name_input, actions=[ft.TextButton("Cancel", on_click=lambda e: self.page.close(self.l3_dialog), style=ft.ButtonStyle(color=TEXT_SUB)), ft.ElevatedButton("Save", on_click=self.save_l3_tab, bgcolor=PRIMARY, color="#FFFFFF", style=btn_style)])
        
        self.prod_dropdown = ft.Dropdown(label="Select Product", border_radius=8, focused_border_color=PRIMARY)
        self.stock_qty_input = ft.TextField(label="Quantity (e.g., 500)", border_radius=8, focused_border_color=PRIMARY)
        self.stock_dialog = ft.AlertDialog(shape=dlg_shape, title=ft.Text("Add Raw Stock", weight=ft.FontWeight.BOLD), content=ft.Column([self.prod_dropdown, self.stock_qty_input], tight=True), actions=[ft.TextButton("Cancel", on_click=lambda e: self.page.close(self.stock_dialog), style=ft.ButtonStyle(color=TEXT_SUB)), ft.ElevatedButton("Import", on_click=self.save_stock, bgcolor=TEXT_MAIN, color="#FFFFFF", style=btn_style)])
        
        self.process_batch_input = ft.TextField(label="Batch Identifier", border_radius=8, focused_border_color=PRIMARY)
        self.process_qty_input = ft.TextField(label="Quantity to Process", border_radius=8, focused_border_color=PRIMARY)
        self.process_dialog = ft.AlertDialog(shape=dlg_shape, title=ft.Text("Start Processing", weight=ft.FontWeight.BOLD), content=ft.Column([self.process_batch_input, self.process_qty_input], tight=True), actions=[ft.TextButton("Cancel", on_click=lambda e: self.page.close(self.process_dialog), style=ft.ButtonStyle(color=TEXT_SUB)), ft.ElevatedButton("Launch Batch", on_click=self.execute_process, bgcolor=PRIMARY, color="#FFFFFF", style=btn_style)])
        
        self.confirm_text = ft.Text("")
        self.confirm_btn = ft.ElevatedButton("Yes", on_click=self.execute_step, bgcolor=PRIMARY, color="#FFFFFF", style=btn_style)
        self.confirm_dialog = ft.AlertDialog(shape=dlg_shape, title=ft.Text("Confirm Action", weight=ft.FontWeight.BOLD), content=self.confirm_text, actions=[ft.TextButton("Cancel", on_click=lambda e: self.page.close(self.confirm_dialog), style=ft.ButtonStyle(color=TEXT_SUB)), self.confirm_btn])
        
        self.custom_step_input = ft.TextField(label="Custom Step Description", border_radius=8, focused_border_color=PRIMARY)
        self.custom_step_pos_input = ft.TextField(label="Insert at Position (Optional)", value="", border_radius=8, focused_border_color=PRIMARY)
        self.step_dialog = ft.AlertDialog(shape=dlg_shape, title=ft.Text("Add Routing Step", weight=ft.FontWeight.BOLD), content=ft.Column([self.custom_step_input, self.custom_step_pos_input], tight=True), actions=[ft.TextButton("Cancel", on_click=lambda e: self.page.close(self.step_dialog), style=ft.ButtonStyle(color=TEXT_SUB)), ft.ElevatedButton("Insert Step", on_click=self.execute_custom_step, bgcolor=TEXT_MAIN, color="#FFFFFF", style=btn_style)])
        
        self.complete_batch_text = ft.Text("Finish this batch and securely log it into history?")
        self.complete_batch_dialog = ft.AlertDialog(shape=dlg_shape, title=ft.Text("Complete Batch", weight=ft.FontWeight.BOLD), content=self.complete_batch_text, actions=[ft.TextButton("Cancel", on_click=lambda e: self.page.close(self.complete_batch_dialog), style=ft.ButtonStyle(color=TEXT_SUB)), ft.ElevatedButton("Yes, Complete", on_click=self.execute_complete_batch, bgcolor=SUCCESS, color="#FFFFFF", style=btn_style)])
        
        self.move_fac_dd = ft.Dropdown(label="1. Destination Factory", on_change=self.on_move_fac_change, border_radius=8, focused_border_color=WARNING)
        self.move_loc_dd = ft.Dropdown(label="2. Destination Room", on_change=self.on_move_loc_change, border_radius=8, focused_border_color=WARNING)
        self.move_sub_dd = ft.Dropdown(label="3. Destination Sub-Zone", border_radius=8, focused_border_color=WARNING)
        self.move_dialog = ft.AlertDialog(shape=dlg_shape, title=ft.Text("Relocate Batch", weight=ft.FontWeight.BOLD), content=ft.Column([self.move_fac_dd, self.move_loc_dd, self.move_sub_dd], tight=True), actions=[ft.TextButton("Cancel", on_click=lambda e: self.page.close(self.move_dialog), style=ft.ButtonStyle(color=TEXT_SUB)), ft.ElevatedButton("Execute Move", on_click=self.execute_move, bgcolor=WARNING, color="#FFFFFF", style=btn_style)])

    def show_snackbar(self, msg, is_error=False): self.page.open(ft.SnackBar(content=ft.Text(msg, color="#FFFFFF", weight=ft.FontWeight.W_500), bgcolor="#EF4444" if is_error else "#10B981", behavior=ft.SnackBarBehavior.FLOATING, margin=20, shape=ft.RoundedRectangleBorder(radius=8)))

    def get_current_data(self):
        factory, loc = self.get_context(); key = f"{factory}::{loc}"
        if key not in self.level3_data: self.level3_data[key] = {"tabs": [], "active_tab": 0, "data": {}}
        for tab_val, tab_data in self.level3_data[key]["data"].items():
            if "stock" not in tab_data: tab_data["stock"] = {}
        return self.level3_data[key]

    def get_item_by_id(self, item_id, return_list=False):
        data_ctx = self.get_current_data()
        if not data_ctx["tabs"]: return None
        active_items = data_ctx["data"][data_ctx["tabs"][data_ctx["active_tab"]]]["active"]
        for item in active_items:
            if item["id"] == item_id: return (item, active_items) if return_list else item
        return None

    def get_all_batch_names(self):
        names = set()
        for loc_data in self.level3_data.values():
            for tab_data in loc_data["data"].values():
                for item in tab_data.get("active", []): names.add(item.get("name"))
                for item in tab_data.get("history", []):
                    if item.get("entry_type") == "Batch": names.add(item.get("name"))
        return names

    def get_unique_batch_name(self):
        existing = self.get_all_batch_names()
        i = 1
        while f"Batch {i}" in existing: i += 1
        return f"Batch {i}"

    def update_context(self): self.render()

    def open_add_l3_dialog(self, e): self.l3_name_input.value = ""; self.page.open(self.l3_dialog)
    def save_l3_tab(self, e):
        val = self.l3_name_input.value.strip()
        if not val: return
        data_ctx = self.get_current_data()
        if val not in data_ctx["tabs"]:
            data_ctx["tabs"].append(val); data_ctx["data"][val] = {"stock": {}, "active": [], "history": []}; data_ctx["active_tab"] = len(data_ctx["tabs"]) - 1
            self.page.close(self.l3_dialog); self.render()
        else: self.show_snackbar("Name already exists!", True)

    def on_l3_tab_change(self, e): 
        data_ctx = self.get_current_data()
        data_ctx["active_tab"] = self.l3_tabs.selected_index
        self.view_mode_tabs.selected_index = 0
        self.expanded_active_groups.clear()
        self.expanded_history_groups.clear()
        self.render()

    def on_view_mode_change(self, e):
        self.expanded_active_groups.clear()
        self.expanded_history_groups.clear()
        self.render_lists(e)

    def open_add_stock_dialog(self, e):
        if not self.products_config: self.show_snackbar("Configure products in Settings first!", True); return
        self.prod_dropdown.options = [ft.dropdown.Option(p) for p in self.products_config.keys()]; self.prod_dropdown.value = None; self.stock_qty_input.value = ""; self.page.open(self.stock_dialog)

    def save_stock(self, e):
        prod_name = self.prod_dropdown.value; qty = parse_qty(self.stock_qty_input.value.strip())
        if not prod_name or qty is None or qty <= 0: return
        data_ctx = self.get_current_data(); tab_data = data_ctx["data"][data_ctx["tabs"][data_ctx["active_tab"]]]
        tab_data["stock"][prod_name] = tab_data["stock"].get(prod_name, 0) + qty
        tab_data["history"].append({"entry_type": "Stock", "type": prod_name, "action": "Added to Stock", "quantity": qty, "date": datetime.now().strftime("%Y-%m-%d %I:%M %p")})
        self.expanded_active_groups.add(prod_name); self.page.close(self.stock_dialog); self.render()

    def open_process_dialog(self, product_name):
        self.current_process_product = product_name; self.process_batch_input.value = self.get_unique_batch_name(); self.process_qty_input.value = ""; self.page.open(self.process_dialog)

    def execute_process(self, e):
        ptype = self.current_process_product; qty = parse_qty(self.process_qty_input.value)
        batch_name = self.process_batch_input.value.strip() or self.get_unique_batch_name()
        if batch_name in self.get_all_batch_names(): self.show_snackbar(f"Batch name '{batch_name}' is already in use!", True); return
        if qty is None or qty <= 0: return
        data_ctx = self.get_current_data(); tab_data = data_ctx["data"][data_ctx["tabs"][data_ctx["active_tab"]]]
        current_stock = tab_data["stock"].get(ptype, 0)
        if qty > current_stock: self.show_snackbar(f"Not enough stock! Only {current_stock:g} available.", True); return
            
        tab_data["stock"][ptype] -= qty
        independent_steps = list(self.products_config.get(ptype, []))
        time_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        tab_data["active"].append({"id": str(uuid.uuid4()), "type": ptype, "name": batch_name, "quantity": qty, "steps": independent_steps, "step_idx": 0, "is_processing": False, "timeline": [{"step": "Created from Stock", "time": time_str}]})
        self.page.close(self.process_dialog); self.render()

    def update_field(self, item_id, field, value):
        item = self.get_item_by_id(item_id)
        if not item: return
        if field == "quantity":
            val = parse_qty(value)
            if val is not None: item[field] = val
        elif field == "name":
            val = value.strip()
            if val in self.get_all_batch_names() and val != item["name"]: self.show_snackbar("This batch name exists elsewhere! Change reverted.", True); self.render(); return
            item[field] = val if val else item[field]
        else: item[field] = value

    def open_confirm_step(self, item_id):
        self.current_action_item = item_id; item = self.get_item_by_id(item_id)
        if item["step_idx"] < len(item["steps"]):
            self.is_finishing_batch = False; step_name = item["steps"][item["step_idx"]]
            if not item.get("is_processing", False): self.confirm_text.value = f"Commence step '{step_name}'?"; self.confirm_btn.text = "Yes, Start"; self.confirm_btn.bgcolor = PRIMARY
            else: self.confirm_text.value = f"Log '{step_name}' as fully completed?"; self.confirm_btn.text = "Yes, Complete"; self.confirm_btn.bgcolor = "#0D9488" 
            self.page.open(self.confirm_dialog)

    def open_custom_step(self, item_id): self.current_action_item = item_id; self.custom_step_input.value = ""; self.custom_step_pos_input.value = ""; self.page.open(self.step_dialog)
    def open_complete_batch(self, item_id): self.current_action_item = item_id; self.page.open(self.complete_batch_dialog)

    def open_move_dialog(self, item_id):
        self.current_action_item = item_id; self.move_fac_dd.options = [ft.dropdown.Option(f) for f in self.factories]
        curr_fac, curr_loc = self.get_context(); self.move_fac_dd.value = curr_fac; self.on_move_fac_change(None); self.move_loc_dd.value = curr_loc; self.on_move_loc_change(None) 
        if self.get_current_data()["tabs"]: self.move_sub_dd.value = self.get_current_data()["tabs"][self.get_current_data()["active_tab"]]
        self.page.open(self.move_dialog)

    def on_move_fac_change(self, e):
        fac = self.move_fac_dd.value; self.move_loc_dd.options = [ft.dropdown.Option(l) for l in self.factory_sub_locations[fac]] if fac and fac in self.factory_sub_locations else []
        self.move_loc_dd.value = None; self.move_sub_dd.options = []; self.move_sub_dd.value = None
        if e: self.page.update()

    def on_move_loc_change(self, e):
        fac, loc = self.move_fac_dd.value, self.move_loc_dd.value
        key = f"{fac}::{loc}"
        if fac and loc and key in self.level3_data and self.level3_data[key]["tabs"]: self.move_sub_dd.options = [ft.dropdown.Option(t) for t in self.level3_data[key]["tabs"]]
        else: self.move_sub_dd.options = []
        self.move_sub_dd.value = None
        if e: self.page.update()

    def execute_move(self, e):
        fac, loc, sub = self.move_fac_dd.value, self.move_loc_dd.value, self.move_sub_dd.value
        if not (fac and loc and sub): return
        curr_fac, curr_loc = self.get_context(); curr_sub = self.get_current_data()["tabs"][self.get_current_data()["active_tab"]]
        item, active_items_list = self.get_item_by_id(self.current_action_item, return_list=True)
        active_items_list.remove(item)
        item["timeline"].append({"step": f"Relocated: [{curr_fac} > {curr_loc} > {curr_sub}] → [{fac} > {loc} > {sub}]", "time": datetime.now().strftime("%Y-%m-%d %I:%M %p")})
        target_key = f"{fac}::{loc}"
        if target_key not in self.level3_data: self.level3_data[target_key] = {"tabs": [sub], "active_tab": 0, "data": {sub: {"stock": {}, "active": [], "history": []}}}
        elif sub not in self.level3_data[target_key]["data"]: self.level3_data[target_key]["tabs"].append(sub); self.level3_data[target_key]["data"][sub] = {"stock": {}, "active": [], "history": []}
        self.level3_data[target_key]["data"][sub]["active"].append(item)
        self.page.close(self.move_dialog); self.show_snackbar("Batch safely relocated!"); self.render()

    def execute_step(self, e):
        item, active_items_list = self.get_item_by_id(self.current_action_item, return_list=True)
        if item["step_idx"] < len(item["steps"]):
            step_name = item["steps"][item["step_idx"]]
            if not item.get("is_processing", False): item["is_processing"] = True; item["timeline"].append({"step": f"Started: {step_name}", "time": datetime.now().strftime("%Y-%m-%d %I:%M %p")})
            else: item["is_processing"] = False; item["timeline"].append({"step": f"Completed: {step_name}", "time": datetime.now().strftime("%Y-%m-%d %I:%M %p")}); item["step_idx"] += 1
        self.page.close(self.confirm_dialog); self.render()

    def execute_custom_step(self, e):
        val = self.custom_step_input.value.strip(); pos_str = self.custom_step_pos_input.value.strip()
        if val:
            item = self.get_item_by_id(self.current_action_item); pos_idx = len(item["steps"]) 
            if pos_str.isdigit():
                pos_idx = int(pos_str) - 1
                if pos_idx < 0: pos_idx = 0
                if pos_idx > len(item["steps"]): pos_idx = len(item["steps"])
            item["steps"].insert(pos_idx, val)
            if pos_idx < item["step_idx"]: item["step_idx"] += 1
            elif pos_idx == item["step_idx"] and item.get("is_processing"): item["step_idx"] += 1
            self.page.close(self.step_dialog); self.render()

    def delete_specific_step(self, item_id, step_idx):
        item = self.get_item_by_id(item_id)
        if item and step_idx < len(item["steps"]): item["steps"].pop(step_idx); self.render()

    def execute_revert(self, item_id):
        item = self.get_item_by_id(item_id)
        if not item: return
        if item.get("is_processing", False):
            item["is_processing"] = False
            if item["timeline"] and "Started:" in item["timeline"][-1]["step"]: item["timeline"].pop()
        elif item["step_idx"] > 0:
            item["step_idx"] -= 1; item["is_processing"] = True
            if item["timeline"] and "Completed:" in item["timeline"][-1]["step"]: item["timeline"].pop()
        self.render()

    def execute_complete_batch(self, e):
        item, active_items_list = self.get_item_by_id(self.current_action_item, return_list=True)
        data_ctx = self.get_current_data(); tab_data = data_ctx["data"][data_ctx["tabs"][data_ctx["active_tab"]]]
        history_item = copy.deepcopy(item); history_item["date_completed"] = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        history_item["timeline"].append({"step": "Batch Finalized & Archived", "time": history_item["date_completed"]})
        history_item["entry_type"] = "Batch"
        tab_data["history"].append(history_item); active_items_list.remove(item) 
        self.expanded_history_groups.add(history_item["type"]); self.page.close(self.complete_batch_dialog); self.render()

    def toggle_group(self, e, ptype, is_active):
        target_set = self.expanded_active_groups if is_active else self.expanded_history_groups
        if e.data == "true": target_set.add(ptype)
        else: target_set.discard(ptype)

    def on_start_date_change(self, e): self.history_start_date = self.start_date_picker.value; self.render_lists(None)
    def on_end_date_change(self, e): self.history_end_date = self.end_date_picker.value; self.render_lists(None)
    def clear_dates(self, e): self.history_start_date = None; self.history_end_date = None; self.render_lists(None)

    def render(self):
        data_ctx = self.get_current_data()
        current_l3_names = [t.text for t in self.l3_tabs.tabs]
        if current_l3_names != data_ctx["tabs"]: self.l3_tabs.tabs = [ft.Tab(text=t) for t in data_ctx["tabs"]]
        self.l3_tabs.selected_index = data_ctx["active_tab"] if data_ctx["tabs"] else 0
        has_tabs = len(data_ctx["tabs"]) > 0
        self.add_stock_btn.visible = has_tabs; self.view_mode_tabs.visible = has_tabs
        if not has_tabs:
            self.list_container.controls = [ft.Container(padding=40, alignment=ft.alignment.center, content=ft.Text("Define a sub-location using the '+' icon above to start managing inventory.", color=TEXT_SUB, size=15))]
        else:
            active_tab_name = data_ctx["tabs"][data_ctx["active_tab"]]
            has_history = len(data_ctx["data"][active_tab_name]["history"]) > 0
            new_view_tab_names = ["Active Matrix"]
            if has_history: new_view_tab_names.append("Archive & Logs")
            current_view_tab_names = [t.text for t in self.view_mode_tabs.tabs]
            if current_view_tab_names != new_view_tab_names: self.view_mode_tabs.tabs = [ft.Tab(text=n) for n in new_view_tab_names]
            if self.view_mode_tabs.selected_index >= len(self.view_mode_tabs.tabs): self.view_mode_tabs.selected_index = 0
            self.render_lists(None)
        if self.page: self.update()
        
        self.save_cb() 

    def render_lists(self, e):
        self.list_container.controls.clear()
        data_ctx = self.get_current_data()
        tab_data = data_ctx["data"][data_ctx["tabs"][data_ctx["active_tab"]]]
        is_history_view = self.view_mode_tabs.selected_index == 1
        
        def make_input(val, lbl, width, on_blur_cb): return ft.TextField(value=val, label=lbl, height=44, content_padding=ft.padding.symmetric(horizontal=12, vertical=5), text_size=13, width=width, expand=(width is None), border_radius=8, border_color="#E2E8F0", focused_border_color=PRIMARY, on_blur=on_blur_cb)

        if is_history_view:
            date_row = ft.Container(padding=15, bgcolor=CARD_BG, border_radius=12, border=ft.border.all(1, BORDER), shadow=ft.BoxShadow(blur_radius=10, color="#00000005", offset=ft.Offset(0, 2)), content=ft.Row([ft.Text("Log Filter:", color=TEXT_SUB, weight=ft.FontWeight.W_500), ft.ElevatedButton(f"Start: {self.history_start_date.strftime('%d %b %Y') if self.history_start_date else 'Any'}", on_click=lambda _: self.start_date_picker.pick_date(), icon=ft.Icons.CALENDAR_TODAY, color=TEXT_MAIN, bgcolor="#F1F5F9", elevation=0, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))), ft.ElevatedButton(f"End: {self.history_end_date.strftime('%d %b %Y') if self.history_end_date else 'Any'}", on_click=lambda _: self.end_date_picker.pick_date(), icon=ft.Icons.CALENDAR_TODAY, color=TEXT_MAIN, bgcolor="#F1F5F9", elevation=0, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))), ft.IconButton(ft.Icons.CLOSE, on_click=self.clear_dates, tooltip="Clear", icon_color="#EF4444", bgcolor="#FEF2F2")], wrap=True)) 
            self.list_container.controls.append(date_row)

            filtered_items = []
            for item in tab_data["history"]:
                dt_str = item.get("date") or item.get("date_completed")
                if not dt_str and "timeline" in item and item["timeline"]: dt_str = item["timeline"][-1]["time"]
                dt = parse_date(dt_str)
                if self.history_start_date and dt.date() < self.history_start_date.date(): continue
                if self.history_end_date and dt.date() > self.history_end_date.date(): continue
                filtered_items.append(item)

            if not filtered_items:
                self.list_container.controls.append(ft.Container(padding=40, alignment=ft.alignment.center, content=ft.Text("No history matching this date range.", color=TEXT_SUB, size=15)))
                if self.page: self.update(); return

            consolidated_batches = {}; stock_logs = []
            for item in filtered_items:
                if item.get("entry_type") == "Stock": stock_logs.append(item)
                else:
                    b_name = item["name"]
                    if b_name not in consolidated_batches: consolidated_batches[b_name] = copy.deepcopy(item)
                    else:
                        consolidated_batches[b_name]["quantity"] += item["quantity"]; existing_times = [log["time"] for log in consolidated_batches[b_name]["timeline"]]
                        for log in item["timeline"]:
                            if log["time"] not in existing_times: consolidated_batches[b_name]["timeline"].append(log); existing_times.append(log["time"])

            for b_name, b_data in consolidated_batches.items():
                b_data["timeline"].sort(key=lambda x: parse_date(x["time"]))
                should_expand = b_data["type"] in self.expanded_history_groups
                logs_ui = []
                for log in b_data["timeline"]:
                    dt_obj = parse_date(log['time'])
                    time_formatted = dt_obj.strftime("%d %b %Y, %I:%M %p")
                    logs_ui.append(ft.Row([ft.Icon(ft.Icons.CIRCLE, size=6, color="#94A3B8"), ft.Text(f"{log['step']}", size=13, color=TEXT_MAIN, expand=True), ft.Text(time_formatted, size=11, color=TEXT_SUB)]))
                
                self.list_container.controls.append(ft.Container(bgcolor=CARD_BG, border_radius=12, border=ft.border.all(1, BORDER), shadow=ft.BoxShadow(blur_radius=8, color="#00000005", offset=ft.Offset(0, 2)), content=ft.ExpansionTile(title=ft.Text(f"{b_data['type']} - {b_name}", weight=ft.FontWeight.W_700, color=TEXT_MAIN), subtitle=ft.Text(f"Archived Qty: {b_data['quantity']:g} | Last update: {b_data['timeline'][-1]['time']}", size=12, color=TEXT_SUB), leading=ft.Container(padding=8, bgcolor="#F0FDF4", border_radius=8, content=ft.Icon(ft.Icons.ARCHIVE_OUTLINED, color=SUCCESS, size=20)), initially_expanded=should_expand, on_change=lambda e, n=b_data["type"]: self.toggle_group(e, n, False), controls_padding=0, controls=[ft.Divider(height=1, color=BORDER), ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=15), bgcolor="#F8FAFC", content=ft.Column(logs_ui, spacing=6))])))

            for item in reversed(stock_logs): 
                is_added = "Added" in item["action"]
                bg_c = "#EFF6FF" if is_added else "#FFF7ED"
                icon_c = PRIMARY if is_added else WARNING
                icon_t = ft.Icons.ADD_SHOPPING_CART if is_added else ft.Icons.PLAY_ARROW
                dt_obj = parse_date(item['date'])
                
                self.list_container.controls.append(ft.Container(bgcolor=CARD_BG, border_radius=12, border=ft.border.all(1, BORDER), padding=ft.padding.symmetric(vertical=5), content=ft.ListTile(leading=ft.Container(padding=8, bgcolor=bg_c, border_radius=8, content=ft.Icon(icon_t, color=icon_c, size=20)), title=ft.Text(f"{item['type']} - {item['action']}", weight=ft.FontWeight.W_600, color=TEXT_MAIN), subtitle=ft.Text(f"Quantity: {item['quantity']:g}", color=TEXT_SUB), trailing=ft.Text(dt_obj.strftime("%d %b %Y, %I:%M %p"), size=12, color=TEXT_SUB))))
        else:
            grouped_products = set(tab_data["stock"].keys())
            for item in tab_data["active"]: grouped_products.add(item["type"])
            if not grouped_products:
                self.list_container.controls.append(ft.Container(padding=40, alignment=ft.alignment.center, content=ft.Text("Inventory is empty. Import stock to begin.", color=TEXT_SUB, size=15)))
                if self.page: self.update(); return

            for ptype in grouped_products:
                curr_stock = tab_data["stock"].get(ptype, 0); p_items = [b for b in tab_data["active"] if b["type"] == ptype]; batch_row = ft.ResponsiveRow(columns=12, spacing=15, run_spacing=15)
                for item in p_items: 
                    name_field = make_input(item["name"], "Batch Tag", None, lambda e, i=item["id"]: self.update_field(i, "name", e.control.value))
                    qty_field = make_input(f"{item['quantity']:g}", "Qty", 80, lambda e, i=item["id"]: self.update_field(i, "quantity", e.control.value))
                    max_steps = len(item["steps"]); step_idx = item["step_idx"]; is_processing = item.get("is_processing", False)
                    
                    steps_visual = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO, height=120 if max_steps > 0 else 10)
                    for idx, s_name in enumerate(item["steps"]):
                        step_time_str = ""
                        if idx < step_idx:
                            icon, color, font_w = ft.Icons.CHECK_CIRCLE, SUCCESS, ft.FontWeight.W_600
                            for log in reversed(item["timeline"]):
                                if log["step"] == f"Completed: {s_name}": 
                                    dt_obj = parse_date(log['time'])
                                    step_time_str = f" • {dt_obj.strftime('%d %b %Y, %I:%M %p')}"
                                    break
                        elif idx == step_idx and is_processing:
                            icon, color, font_w = ft.Icons.MOTION_PHOTOS_ON, WARNING, ft.FontWeight.W_700
                            for log in reversed(item["timeline"]):
                                if log["step"] == f"Started: {s_name}": 
                                    dt_obj = parse_date(log['time'])
                                    step_time_str = f" • {dt_obj.strftime('%d %b %Y, %I:%M %p')}"
                                    break
                        elif idx == step_idx and not is_processing: icon, color, font_w = ft.Icons.RADIO_BUTTON_UNCHECKED, PRIMARY, ft.FontWeight.W_600
                        else: icon, color, font_w = ft.Icons.RADIO_BUTTON_UNCHECKED, "#CBD5E1", ft.FontWeight.W_400
                            
                        can_delete = (idx > step_idx) or (idx == step_idx and not is_processing)
                        del_btn = ft.IconButton(ft.Icons.CLOSE, icon_color="#EF4444", icon_size=12, padding=0, width=16, height=16, on_click=lambda e, i=item["id"], s_i=idx: self.delete_specific_step(i, s_i))
                        steps_visual.controls.append(ft.Container(padding=ft.padding.only(left=5, right=5, top=4, bottom=4), border_radius=6, bgcolor="#F8FAFC" if (idx == step_idx) else ft.colors.TRANSPARENT, content=ft.Row([ft.Icon(icon, color=color, size=16), ft.Text(f"{s_name}", size=13, color=TEXT_MAIN if color != "#CBD5E1" else TEXT_SUB, weight=font_w, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS), ft.Text(step_time_str, size=10, color=TEXT_SUB), del_btn if can_delete else ft.Container(width=16)])))

                    show_move = False
                    if step_idx >= max_steps: btn_text, btn_color, next_btn_disabled = "Ready to Archive", "#CBD5E1", True 
                    else: btn_text, btn_color, next_btn_disabled, show_move = (f"Finish Step" if is_processing else f"Start Step"), ("#0D9488" if is_processing else PRIMARY), False, not is_processing 

                    btn_style = ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=ft.padding.symmetric(horizontal=12))
                    add_step_btn = ft.IconButton(ft.Icons.ADD, tooltip="Inject routing step", icon_color=PRIMARY, bgcolor="#EFF6FF", icon_size=16, padding=0, width=28, height=28, on_click=lambda e, i=item["id"]: self.open_custom_step(i))
                    undo_btn = ft.IconButton(ft.Icons.UNDO, tooltip="Revert Last Action", icon_color=TEXT_SUB, hover_color="#F1F5F9", padding=0, width=32, height=32, on_click=lambda e, i=item["id"]: self.execute_revert(i))
                    move_btn = ft.IconButton(ft.Icons.DRIVE_FILE_MOVE_OUTLINE, tooltip="Relocate Batch", icon_color=WARNING, bgcolor="#FFFBEB", padding=0, width=32, height=32, on_click=lambda e, i=item["id"]: self.open_move_dialog(i))
                    next_btn = ft.ElevatedButton(btn_text, disabled=next_btn_disabled, color="#FFFFFF", bgcolor=btn_color, style=btn_style, on_click=lambda e, i=item["id"]: self.open_confirm_step(i))
                    complete_batch_btn = ft.ElevatedButton("Archive", color="#FFFFFF", bgcolor=SUCCESS, style=btn_style, on_click=lambda e, i=item["id"]: self.open_complete_batch(i))

                    card = ft.Container(bgcolor=CARD_BG, border_radius=12, border=ft.border.all(1, BORDER), shadow=ft.BoxShadow(blur_radius=10, color="#00000008", offset=ft.Offset(0, 4)), content=ft.Column([ft.Container(padding=15, content=ft.Column([ft.Row([name_field, qty_field]), ft.Divider(height=20, color="#F1F5F9"), steps_visual, ft.Container(height=5), ft.Row([ft.Text("Inject manual step:", size=11, color=TEXT_SUB, weight=ft.FontWeight.W_500), add_step_btn], alignment=ft.MainAxisAlignment.START)])), ft.Container(padding=12, bgcolor="#F8FAFC", border_radius=ft.border_radius.only(bottom_left=12, bottom_right=12), border=ft.border.only(top=ft.border.BorderSide(1, BORDER)), content=ft.Row([complete_batch_btn, ft.Row([undo_btn if (step_idx > 0 or is_processing) else ft.Container(), move_btn if show_move else ft.Container(), next_btn], spacing=5, wrap=True)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True))], spacing=0))
                    batch_row.controls.append(ft.Column(col={"xs": 12, "md": 6, "xl": 4}, controls=[card]))

                should_expand = (ptype in self.expanded_active_groups) or len(grouped_products) == 1 
                btn_style_send = ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=ft.padding.symmetric(horizontal=15))
                process_btn = ft.ElevatedButton("Extract to Batch", icon=ft.Icons.CALL_SPLIT, color="#FFFFFF", bgcolor=TEXT_MAIN, style=btn_style_send, on_click=lambda e, p=ptype: self.open_process_dialog(p), disabled=(curr_stock <= 0))
                
                tile = ft.Container(bgcolor=CARD_BG, border_radius=12, border=ft.border.all(1, BORDER), shadow=ft.BoxShadow(blur_radius=10, color="#00000005", offset=ft.Offset(0, 2)), content=ft.ExpansionTile(title=ft.Text(f"{ptype}", size=18, weight=ft.FontWeight.W_800, color=TEXT_MAIN), subtitle=ft.Text(f"Available Stock: {curr_stock:g} units | Processing: {len(p_items)} batches", color=PRIMARY if curr_stock > 0 else TEXT_SUB, weight=ft.FontWeight.W_500), leading=ft.Container(padding=10, bgcolor="#EFF6FF", border_radius=8, content=ft.Icon(ft.Icons.CATEGORY_OUTLINED, color=PRIMARY, size=24)), initially_expanded=should_expand, on_change=lambda e, p=ptype: self.toggle_group(e, p, True), controls_padding=0, trailing=process_btn, controls=[ft.Divider(height=1, color=BORDER), ft.Container(padding=20, bgcolor="#F8FAFC", content=batch_row if p_items else ft.Text("No active operations. Extract stock to begin.", color=TEXT_SUB))]))
                self.list_container.controls.append(tile)

        if self.page: self.update()