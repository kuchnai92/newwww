import flet as ft

class FactoryHeader(ft.Column):
    def __init__(self, on_tab_change, on_add_click, on_edit_click, on_delete_click, on_menu_click):
        super().__init__()
        self.spacing = 0
        self.is_visible = True
        self.on_tab_change = on_tab_change
        
        self.menu_btn = ft.IconButton(icon=ft.Icons.MENU, icon_color="#FFFFFF", on_click=on_menu_click, visible=False)
        
        self.tabs = ft.Tabs(
            selected_index=0, animation_duration=300, on_change=self.handle_tab_change,
            tabs=[], label_color="#FFFFFF", unselected_label_color="#94A3B8", 
            indicator_color="#38BDF8", indicator_padding=ft.padding.only(bottom=5),
        )

        btn_style = ft.ButtonStyle(shape=ft.CircleBorder())
        self.add_btn = ft.IconButton(icon=ft.Icons.ADD, icon_color="#FFFFFF", bgcolor="#3B82F6", tooltip="Add Factory", on_click=on_add_click, style=btn_style)
        self.edit_btn = ft.IconButton(icon=ft.Icons.EDIT, icon_color="#94A3B8", tooltip="Edit Active Factory", on_click=on_edit_click, style=btn_style)
        self.delete_btn = ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="#F87171", tooltip="Delete Active Factory", on_click=on_delete_click, style=btn_style)

        self.bar_container = ft.Container(
            content=ft.Row(
                controls=[
                    self.menu_btn,
                    ft.Container(
                        padding=8, bgcolor="#334155", border_radius=8,
                        content=ft.Icon(ft.Icons.FACTORY, color="#60A5FA", size=20)
                    ),
                    ft.Container(width=10),
                    ft.Container(content=self.tabs, expand=True),
                    self.edit_btn, self.delete_btn, ft.Container(width=5), self.add_btn
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor="#0F172A", 
            height=65, padding=ft.padding.symmetric(horizontal=10, vertical=0),
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            shadow=ft.BoxShadow(blur_radius=10, color="#00000040", offset=ft.Offset(0, 4)),
        )

        self.arrow_icon = ft.IconButton(
            icon=ft.Icons.KEYBOARD_ARROW_UP, icon_color="#64748B", bgcolor="#FFFFFF", on_click=self.toggle_bar,
            style=ft.ButtonStyle(shape=ft.CircleBorder(), elevation=3)
        )
        self.arrow_handle = ft.Container(content=self.arrow_icon, alignment=ft.alignment.center, margin=ft.margin.only(top=-20), height=40)
        self.controls = [self.bar_container, self.arrow_handle]

    def set_menu_visible(self, is_visible):
        self.menu_btn.visible = is_visible
        self.update()

    def handle_tab_change(self, e):
        if self.tabs.tabs: self.on_tab_change(self.tabs.selected_index)

    def update_tabs(self, locations, active_index):
        current_tab_names = [t.text for t in self.tabs.tabs]
        if current_tab_names != locations:
            self.tabs.tabs = [ft.Tab(text=loc) for loc in locations]
        self.tabs.selected_index = active_index
        self.edit_btn.visible = len(locations) > 0
        self.delete_btn.visible = len(locations) > 0
        self.update()

    def toggle_bar(self, e):
        self.is_visible = not self.is_visible
        self.bar_container.height = 65 if self.is_visible else 0
        self.bar_container.opacity = 1 if self.is_visible else 0
        self.arrow_icon.icon = ft.Icons.KEYBOARD_ARROW_UP if self.is_visible else ft.Icons.KEYBOARD_ARROW_DOWN
        self.update()