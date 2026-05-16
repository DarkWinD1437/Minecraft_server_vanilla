from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, Button, Input, Select, Switch, Collapsible, Static
from textual.containers import Horizontal, Vertical, ScrollableContainer

from mc_manager.core.config import app_config
from mc_manager.features.settings.properties_parser import (
    read_properties, write_properties, get_sections, PROPERTY_METADATA
)


class SettingsPane(Widget):

    DEFAULT_CSS = """
    SettingsPane {
        width: 100%;
        height: 100%;
        layout: vertical;
        padding: 0 1;
    }
    .settings-toolbar {
        layout: horizontal;
        height: 3;
        background: $panel-darken-1;
        padding: 0 1;
        align: left middle;
        margin-bottom: 1;
    }
    .settings-toolbar Button {
        margin-right: 1;
    }
    #settings-scroll {
        height: 1fr;
    }
    .settings-title {
        text-style: bold;
        color: $accent;
    }
    .settings-warning {
        background: $warning-darken-2;
        color: $text;
        padding: 0 1;
        margin-bottom: 1;
    }
    .prop-row {
        layout: horizontal;
        height: 3;
        align: left middle;
        margin-bottom: 0;
        padding: 0 1;
    }
    .prop-label {
        width: 28;
        color: $text-muted;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._props: dict[str, str] = {}
        self._edits: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        with Horizontal(classes="settings-toolbar"):
            yield Label("⚙️  Configuración", classes="settings-title")
            yield Button("💾 Guardar", id="cfg-save", variant="primary")
            yield Button("🔄 Recargar", id="cfg-reload", variant="default")
            yield Button("↩ Resetear", id="cfg-reset", variant="warning")

        yield Label(
            "⚠ Algunos cambios requieren reiniciar el servidor.",
            classes="settings-warning"
        )
        yield ScrollableContainer(id="settings-scroll")

    def on_mount(self) -> None:
        self.run_worker(self._load_props(), exclusive=True)

    async def _load_props(self) -> None:
        props_path = app_config.server_properties
        scroll = self.query_one("#settings-scroll", ScrollableContainer)
        await scroll.remove_children()

        if not props_path.exists():
            await scroll.mount(
                Static(
                    "⚠ No se encontró server.properties.\n"
                    "El servidor debe haberse iniciado al menos una vez.",
                    classes="settings-warning"
                )
            )
            return

        self._props = read_properties(props_path)
        self._edits = dict(self._props)
        await self._build_form()

    async def _build_form(self) -> None:
        sections = get_sections(self._props)
        scroll = self.query_one("#settings-scroll", ScrollableContainer)

        for section_name, entries in sections.items():
            section_widgets: list[Widget] = []
            for key, value, meta in entries:
                label_text = meta.description if meta else key
                prop_type = meta.prop_type if meta else "str"
                widget_id = f"prop-{key.replace('.', '-')}"

                if prop_type == "bool":
                    checked = value.lower() in ("true", "1", "yes")
                    row = Horizontal(
                        Label(label_text, classes="prop-label"),
                        Switch(value=checked, id=widget_id),
                        classes="prop-row"
                    )
                elif prop_type == "select" and meta and meta.choices:
                    options = [(c, c) for c in meta.choices]
                    safe_value = value if value in meta.choices else meta.choices[0]
                    row = Horizontal(
                        Label(label_text, classes="prop-label"),
                        Select(options=options, value=safe_value, id=widget_id, allow_blank=False),
                        classes="prop-row"
                    )
                else:
                    row = Horizontal(
                        Label(label_text, classes="prop-label"),
                        Input(value=str(value), id=widget_id, placeholder=key),
                        classes="prop-row"
                    )
                section_widgets.append(row)

            coll = Collapsible(
                *section_widgets,
                title=f"📂 {section_name}",
                id=f"section-{section_name.lower().replace(' ', '-')}"
            )
            await scroll.mount(coll)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "cfg-save":
            await self._save()
        elif bid == "cfg-reload":
            await self._load_props()
        elif bid == "cfg-reset":
            self._edits = dict(self._props)
            await self._load_props()

    async def _save(self) -> None:
        for key in list(self._edits.keys()):
            widget_id = f"prop-{key.replace('.', '-')}"
            try:
                meta = PROPERTY_METADATA.get(key)
                if meta and meta.prop_type == "bool":
                    try:
                        sw = self.query_one(f"#{widget_id}", Switch)
                        self._edits[key] = "true" if sw.value else "false"
                    except Exception:
                        pass
                elif meta and meta.prop_type == "select":
                    try:
                        sel = self.query_one(f"#{widget_id}", Select)
                        self._edits[key] = str(sel.value)
                    except Exception:
                        pass
                else:
                    try:
                        inp = self.query_one(f"#{widget_id}", Input)
                        self._edits[key] = inp.value
                    except Exception:
                        pass
            except Exception:
                pass

        try:
            write_properties(app_config.server_properties, self._edits)
            self._props = dict(self._edits)
            self.app.notify("Configuración guardada correctamente", severity="information")
        except Exception as e:
            self.app.notify(f"Error al guardar: {e}", severity="error")

    def on_switch_changed(self, event: Switch.Changed) -> None:
        if event.switch.id and event.switch.id.startswith("prop-"):
            key = event.switch.id[5:].replace("-", ".")
            self._edits[key] = "true" if event.value else "false"

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id and event.input.id.startswith("prop-"):
            key = event.input.id[5:].replace("-", ".")
            self._edits[key] = event.value

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id and event.select.id.startswith("prop-"):
            key = event.select.id[5:].replace("-", ".")
            self._edits[key] = str(event.value)
