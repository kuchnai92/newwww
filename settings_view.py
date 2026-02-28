import flet as ft
import json

class SettingsView(ft.Container):
    def __init__(self, page: ft.Page, products_config: dict, save_cb):
        super().__init__()
        self.page = page
        self.padding = 15 # Optimized for mobile 
        self.expand = True
        self.visible = False
        
        self.save_cb = save_cb 
        self.products = products_config
        self.expanded_products = set() 

        # --- FILE PICKER FOR EXPORT ---
        self.export_picker = ft.FilePicker(on_result=self.on_export_result)
        self.page.overlay.append(self.export_picker)

        self.product_name_input = ft.TextField(
            label="New Product Name", expand=True, 
            border_radius=8, border_color="#CBD5E1", focused_border_color="#2563EB", cursor_color="#2563EB"
        )
        self.add_product_btn = ft.ElevatedButton(
            "Create Product", icon=ft.Icons.ADD, on_click=self.add_product, 
            bgcolor="#2563EB", color="#FFFFFF", height=48, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        
        # --- NEW BACKUP BUTTON ---
        self.export_btn = ft.ElevatedButton(
            "Backup Database", icon=ft.Icons.DOWNLOAD, 
            on_click=lambda _: self.export_picker.save_file(dialog_title="Save ERP Backup", file_name="amin_erp_backup.json", allowed_extensions=["json"]), 
            bgcolor="#10B981", color="#FFFFFF", height=48, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )

        self.products_grid = ft.ResponsiveRow(columns=12, spacing=15, run_spacing=15)
        self.products_list = ft.ListView(controls=[self.products_grid], expand=True, spacing=15, padding=ft.padding.only(bottom=40))

        self.content = ft.Column(
            expand=True,
            controls=[
                ft.Row([
                    ft.Column([
                        ft.Text("Product Setup Matrix", size=24, weight=ft.FontWeight.W_800, color="#0F172A"),
                        ft.Text("Define global routing and processing steps.", size=13, color="#64748B"),
                    ], expand=True),
                    self.export_btn # Placed neatly at the top right
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=10),
                ft.Container(
                    padding=15, bgcolor="#FFFFFF", border_radius=12, border=ft.border.all(1, "#E2E8F0"), shadow=ft.BoxShadow(blur_radius=10, color="#00000008", offset=ft.Offset(0, 4)),
                    content=ft.ResponsiveRow([
                        ft.Column(col={"xs": 12, "sm": 8}, controls=[self.product_name_input]),
                        ft.Column(col={"xs": 12, "sm": 4}, controls=[self.add_product_btn])
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
                ),
                ft.Container(height=10),
                self.products_list
            ]
        )
        
        self.edit_input = ft.TextField(label="Edit Name", autofocus=True, border_radius=8, border_color="#CBD5E1", focused_border_color="#2563EB")
        self.current_edit_data = None 

        self.edit_dialog = ft.AlertDialog(
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Text("Edit", weight=ft.FontWeight.BOLD), content=self.edit_input,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(self.edit_dialog), style=ft.ButtonStyle(color="#64748B")),
                ft.ElevatedButton("Save", on_click=self.save_edit, bgcolor="#2563EB", color="#FFFFFF", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))),
            ],
        )

    # --- NATIVE FILE SAVER LOGIC ---
    def on_export_result(self, e: ft.FilePickerResultEvent):
        if e.path:
            try:
                # Fetch the absolute latest full DB from client storage
                data = self.page.client_storage.get("erp_data")
                if not data:
                    data = {"error": "No data found"}
                
                # Write it to the location the user tapped in the Android menu
                with open(e.path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                self.show_snackbar("Database exported successfully!")
            except Exception as ex:
                self.show_snackbar(f"Failed to export: {ex}", is_error=True)

    def show_snackbar(self, msg, is_error=False):
        self.page.open(ft.SnackBar(content=ft.Text(msg, color="#FFFFFF", weight=ft.FontWeight.W_500), bgcolor="#EF4444" if is_error else "#10B981", behavior=ft.SnackBarBehavior.FLOATING, margin=20, shape=ft.RoundedRectangleBorder(radius=8)))

    def add_product(self, e):
        name = self.product_name_input.value.strip()
        if name and name not in self.products:
            self.products[name] = []; self.expanded_products.add(name); self.product_name_input.value = ""; self.render_products(); self.show_snackbar(f"Product '{name}' added!")
        else: self.show_snackbar("Name invalid or already exists!", True)

    def add_step(self, product_name, step_name, input_field):
        if step_name: self.products[product_name].append(step_name); self.expanded_products.add(product_name); input_field.value = ""; self.render_products()

    def open_edit(self, edit_type, product_name, step_index=None):
        self.current_edit_data = {"type": edit_type, "product": product_name, "step": step_index}
        self.edit_input.value = product_name if edit_type == "product" else self.products[product_name][step_index]
        self.page.open(self.edit_dialog)

    def save_edit(self, e):
        new_val = self.edit_input.value.strip()
        if not new_val: self.show_snackbar("Name cannot be empty!", True); return
        data = self.current_edit_data
        if data["type"] == "product":
            if new_val != data["product"] and new_val in self.products: self.show_snackbar("Product already exists!", True); return
            self.products[new_val] = self.products.pop(data["product"])
            if data["product"] in self.expanded_products: self.expanded_products.remove(data["product"]); self.expanded_products.add(new_val)
        elif data["type"] == "step": self.products[data["product"]][data["step"]] = new_val
        self.page.close(self.edit_dialog); self.render_products(); self.show_snackbar("Updated successfully!")

    def delete_step(self, product_name, step_index): self.products[product_name].pop(step_index); self.render_products()
    def delete_product(self, product_name): del self.products[product_name]; self.expanded_products.discard(product_name); self.render_products()
    def handle_expansion(self, e, prod_name):
        if e.data == "true": self.expanded_products.add(prod_name)
        else: self.expanded_products.discard(prod_name)

    def render_products(self):
        self.products_grid.controls.clear()
        
        for prod_name, steps in self.products.items():
            steps_column = ft.Column(spacing=0)
            for i, step in enumerate(steps):
                steps_column.controls.append(
                    ft.Container(
                        padding=ft.padding.only(left=10, top=8, bottom=8), 
                        border=ft.border.only(bottom=ft.border.BorderSide(1, "#F1F5F9")),
                        content=ft.Row([
                            ft.Container(padding=6, bgcolor="#EFF6FF", border_radius=20, content=ft.Text(str(i+1), size=11, color="#2563EB", weight=ft.FontWeight.BOLD)),
                            ft.Text(step, expand=True, size=13, color="#334155", weight=ft.FontWeight.W_500, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.IconButton(ft.Icons.EDIT, icon_color="#60A5FA", icon_size=16, padding=0, width=30, on_click=lambda e, p=prod_name, idx=i: self.open_edit("step", p, idx)),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="#F87171", icon_size=16, padding=0, width=30, on_click=lambda e, p=prod_name, idx=i: self.delete_step(p, idx))
                        ]) 
                    )
                )

            step_input = ft.TextField(label="Add routing step", expand=True, border_radius=8, content_padding=10, text_size=13, border_color="#E2E8F0", focused_border_color="#2563EB")
            add_step_btn = ft.IconButton(ft.Icons.ADD, icon_color="#FFFFFF", bgcolor="#2563EB", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), on_click=lambda e, p=prod_name, inp=step_input: self.add_step(p, inp.value.strip(), inp))
            steps_column.controls.append(ft.Container(padding=ft.padding.only(left=10, right=10, top=10, bottom=15), content=ft.Row([step_input, add_step_btn])))

            card = ft.Container(
                bgcolor="#FFFFFF", border_radius=12, border=ft.border.all(1, "#E2E8F0"), shadow=ft.BoxShadow(blur_radius=10, color="#00000008", offset=ft.Offset(0, 4)),
                content=ft.ExpansionTile(
                    title=ft.Text(prod_name, size=16, weight=ft.FontWeight.W_700, color="#0F172A"),
                    leading=ft.Container(padding=8, bgcolor="#F8FAFC", border_radius=8, content=ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, color="#64748B", size=20)),
                    controls_padding=0, initially_expanded=(prod_name in self.expanded_products),
                    on_change=lambda e, p=prod_name: self.handle_expansion(e, p),
                    trailing=ft.Row([
                        ft.IconButton(ft.Icons.EDIT, icon_color="#60A5FA", on_click=lambda e, p=prod_name: self.open_edit("product", p)),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="#F87171", on_click=lambda e, p=prod_name: self.delete_product(p)),
                    ], tight=True),
                    controls=[ft.Divider(height=1, color="#E2E8F0"), steps_column]
                )
            )
            self.products_grid.controls.append(ft.Column(col={"xs": 12, "md": 6, "xl": 4}, controls=[card]))
        
        if self.page: self.update()
        self.save_cb()