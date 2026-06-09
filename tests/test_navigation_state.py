from __future__ import annotations

import main


class _Context:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _SessionState(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


class _FakeStreamlit:
    def __init__(self, *, radio_value: str = "Market Desk", button_target: str | None = None):
        self.session_state = _SessionState()
        self.query_params: dict[str, str] = {}
        self._radio_value = radio_value
        self._button_target = button_target
        self.sidebar = _Context()
        self.rerun_called = False

    def markdown(self, *args, **kwargs):
        return None

    def radio(self, label, options, key, label_visibility=None):
        self.session_state[key] = self._radio_value
        return self._radio_value

    def selectbox(self, label, options, key):
        current = self.session_state.get(key)
        if current not in options:
            current = options[0]
            self.session_state[key] = current
        return current

    def caption(self, *args, **kwargs):
        return None

    def columns(self, count):
        return [_Context() for _ in range(count)]

    def button(self, label, key=None, use_container_width=None):
        return label == self._button_target

    def checkbox(self, label, key=None, help=None):
        self.session_state.setdefault(key, False)
        return self.session_state[key]

    def rerun(self):
        self.rerun_called = True
        raise RuntimeError("rerun")


def test_navigation_group_switch_selects_first_workspace(monkeypatch):
    fake_st = _FakeStreamlit(radio_value="Research")
    monkeypatch.setattr(main, "st", fake_st)

    selected_workspace = main.render_primary_navigation()

    assert selected_workspace == "🔍 Stock Research"
    assert fake_st.session_state["primary_workspace_nav"] == "🔍 Stock Research"
    assert fake_st.session_state["workspace_group_nav"] == "Research"
    assert fake_st.session_state["workspace_page_nav"] == "🔍 Stock Research"
    assert fake_st.query_params["view"] == "stock-research"


def test_quick_route_forces_group_and_page_sync_on_rerun(monkeypatch):
    fake_st = _FakeStreamlit(button_target="🔍 Stock Research")
    monkeypatch.setattr(main, "st", fake_st)

    try:
        main.render_primary_navigation()
    except RuntimeError as exc:
        assert str(exc) == "rerun"
    else:
        raise AssertionError("Expected rerun to be triggered for quick-route navigation.")

    assert fake_st.rerun_called is True
    assert fake_st.session_state["primary_workspace_nav"] == "🔍 Stock Research"
    assert fake_st.session_state["_force_nav_sync_workspace"] == "🔍 Stock Research"
    assert fake_st.query_params["view"] == "stock-research"

    fake_st._button_target = None
    fake_st._radio_value = "Research"

    selected_workspace = main.render_primary_navigation()

    assert selected_workspace == "🔍 Stock Research"
    assert fake_st.session_state["workspace_group_nav"] == "Research"
    assert fake_st.session_state["workspace_page_nav"] == "🔍 Stock Research"
