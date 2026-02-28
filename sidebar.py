import flet as ft

class Sidebar(ft.Container):
    def __init__(self, on_nav_change, on_add_click, on_edit_click, on_delete_click):
        super().__init__()
        self.width = 260 
        self.bgcolor = "#FFFFFF"
        self.padding = ft.padding.all(15)
        
        # Make it act like a drawer with shadow and animation
        self.shadow = ft.BoxShadow(blur_radius=20, color="#00000030", offset=ft.Offset(2, 0))
        self.animate_position = ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT)
        
        self.on_nav_change = on_nav_change
        self.on_add_click = on_add_click
        self.on_edit_click = on_edit_click
        self.on_delete_click = on_delete_click
        
        self.nav_column = ft.Column(spacing=8, expand=True, scroll=ft.ScrollMode.AUTO)
        self.content = self.nav_column
        
        self.selected_index = 0
        self.sub_locations = []
        
    def update_locations(self, sub_locations, selected_index):
        self.sub_locations = sub_locations
        self.selected_index = selected_index
        self.render()
        
    def render(self):
        self.nav_column.controls.clear()
        
        self.nav_column.controls.append(
            ft.Container(
                padding=ft.padding.only(bottom=10, left=5),
                content=ft.Row([
                    ft.Icon(ft.Icons.SPACE_DASHBOARD_ROUNDED, color="#2563EB", size=28),
                    ft.Text("ERP Pro", size=20, weight=ft.FontWeight.W_900, color="#0F172A")
                ])
            )
        )
        self.nav_column.controls.append(ft.Divider(height=1, color="#E2E8F0"))
        self.nav_column.controls.append(ft.Container(height=5))
        
        self.nav_column.controls.append(self.create_item(ft.Icons.DASHBOARD_OUTLINED, "Dashboard", 0))
        self.nav_column.controls.append(self.create_item(ft.Icons.SETTINGS_OUTLINED, "Settings", 1))
        
        self.nav_column.controls.append(ft.Container(height=10))
        
        self.nav_column.controls.append(
            ft.Container(
                padding=ft.padding.only(left=10, bottom=5),
                content=ft.Text("LOCATIONS", size=11, weight=ft.FontWeight.BOLD, color="#94A3B8")
            )
        )
        
        for i, loc in enumerate(self.sub_locations):
            actual_index = i + 2
            self.nav_column.controls.append(self.create_item(ft.Icons.FOLDER_OUTLINED, loc, actual_index, is_custom=True))
            
        self.nav_column.controls.append(ft.Container(expand=True)) 
        self.nav_column.controls.append(ft.Divider(height=1, color="#E2E8F0"))
        
        add_btn = ft.Container(
            content=ft.Row([ft.Icon(ft.Icons.ADD, size=20, color="#2563EB"), ft.Text("New Location", size=14, color="#2563EB", weight=ft.FontWeight.W_600)], alignment=ft.MainAxisAlignment.CENTER),
            padding=12, border_radius=8, bgcolor="#EFF6FF", ink=True,
            on_click=lambda e: self.on_add_click()
        )
        self.nav_column.controls.append(add_btn)
        self.update()
        
    def create_item(self, icon, label, index, is_custom=False):
        is_selected = self.selected_index == index
        
        bg = "#EFF6FF" if is_selected else ft.colors.TRANSPARENT
        text_color = "#2563EB" if is_selected else "#475569"
        icon_color = "#2563EB" if is_selected else "#94A3B8"
        weight = ft.FontWeight.W_600 if is_selected else ft.FontWeight.W_500
        
        controls = [
            ft.Icon(icon, color=icon_color, size=20),
            ft.Text(label, color=text_color, size=14, weight=weight, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
        ]
        
        if is_custom:
            controls.extend([
                ft.IconButton(ft.Icons.EDIT, icon_size=14, icon_color="#60A5FA", padding=0, width=24, height=24, on_click=lambda e: self.on_edit_click(index)),
                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=14, icon_color="#F87171", padding=0, width=24, height=24, on_click=lambda e: self.on_delete_click(index))
            ])
            
        return ft.Container(
            content=ft.Row(controls, spacing=10),
            bgcolor=bg, padding=ft.padding.symmetric(horizontal=12, vertical=10), border_radius=8, ink=True,
            on_click=lambda e: self.on_nav_change(index)
        )