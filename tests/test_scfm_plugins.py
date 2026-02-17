"""
Tests for SCFM Plugin System

Tests cover:
- Built-in adapter resolution via get_adapter_class()
- Entry-point plugin discovery (mocked)
- Local directory plugin loading
- Conflict resolution (built-in wins, local overrides entry-point)
- Error handling for malformed plugins
"""

import importlib.metadata
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pantheon.toolsets.scfm.adapters.base import BaseAdapter
from pantheon.toolsets.scfm.registry import (
    ModelRegistry,
    ModelSpec,
    OutputKeys,
    SkillReadyStatus,
    TaskType,
    Modality,
    GeneIDScheme,
    HardwareRequirements,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_spec(name: str = "test_plugin_model", **kwargs) -> ModelSpec:
    """Create a minimal ModelSpec for testing."""
    defaults = dict(
        name=name,
        version="0.1.0",
        skill_ready=SkillReadyStatus.PARTIAL,
        tasks=[TaskType.EMBED],
        modalities=[Modality.RNA],
        species=["human"],
        gene_id_scheme=GeneIDScheme.SYMBOL,
        zero_shot_embedding=True,
        output_keys=OutputKeys(embedding_key=f"X_{name}"),
        embedding_dim=256,
        hardware=HardwareRequirements(gpu_required=False, min_vram_gb=0, cpu_fallback=True),
    )
    defaults.update(kwargs)
    return ModelSpec(**defaults)


class DummyAdapter(BaseAdapter):
    """Minimal adapter for testing."""

    def __init__(self, checkpoint_dir=None):
        # Use a throwaway spec; real plugins would use their own
        spec = _make_spec("dummy")
        super().__init__(spec, checkpoint_dir)

    def run(self, task, adata_path, output_path, **kwargs):
        return {"status": "ok"}

    def _load_model(self, device):
        pass

    def _preprocess(self, adata, task):
        pass

    def _postprocess(self, adata, embeddings, task):
        return []


def _fresh_registry(**kwargs) -> ModelRegistry:
    """Create a fresh ModelRegistry (bypasses global singleton)."""
    return ModelRegistry(**kwargs)


# ---------------------------------------------------------------------------
# Built-in adapter resolution
# ---------------------------------------------------------------------------

class TestBuiltinAdapterResolution:
    """Test that built-in models resolve via get_adapter_class()."""

    def test_builtin_adapter_class_resolves(self):
        registry = _fresh_registry()
        cls = registry.get_adapter_class("scgpt")
        assert cls is not None
        assert cls.__name__ == "ScGPTAdapter"

    def test_builtin_adapter_class_cached(self):
        registry = _fresh_registry()
        cls1 = registry.get_adapter_class("scgpt")
        cls2 = registry.get_adapter_class("scgpt")
        assert cls1 is cls2

    def test_builtin_unknown_model_returns_none(self):
        registry = _fresh_registry()
        cls = registry.get_adapter_class("nonexistent_model_xyz")
        assert cls is None

    def test_all_builtin_names_have_specs(self):
        registry = _fresh_registry()
        for name in registry._builtin_adapter_imports:
            spec = registry.get(name)
            assert spec is not None, f"Built-in adapter '{name}' has no ModelSpec"


# ---------------------------------------------------------------------------
# Plugin registration via register() API
# ---------------------------------------------------------------------------

class TestPluginRegistration:
    """Test the register() method with adapter_class and source params."""

    def test_register_plugin_model(self):
        registry = _fresh_registry()
        spec = _make_spec("myplugin")
        registry.register(spec, DummyAdapter, source="entrypoint:test")
        assert registry.get("myplugin") is spec
        assert registry.get_adapter_class("myplugin") is DummyAdapter

    def test_builtin_protected_from_override(self):
        registry = _fresh_registry()
        original_spec = registry.get("scgpt")
        fake_spec = _make_spec("scgpt")
        registry.register(fake_spec, DummyAdapter, source="entrypoint:evil")
        # Built-in should still be there
        assert registry.get("scgpt") is original_spec
        assert registry.get_adapter_class("scgpt").__name__ == "ScGPTAdapter"

    def test_plugin_overrides_plugin(self):
        registry = _fresh_registry()
        spec1 = _make_spec("myplugin", version="1.0")
        spec2 = _make_spec("myplugin", version="2.0")

        class Adapter1(DummyAdapter):
            pass

        class Adapter2(DummyAdapter):
            pass

        registry.register(spec1, Adapter1, source="entrypoint:pkg1")
        registry.register(spec2, Adapter2, source="local:override.py")
        assert registry.get("myplugin").version == "2.0"
        assert registry.get_adapter_class("myplugin") is Adapter2


# ---------------------------------------------------------------------------
# Entry-point discovery (mocked)
# ---------------------------------------------------------------------------

class TestEntryPointDiscovery:
    """Test _discover_entry_point_plugins with mocked entry points."""

    def test_entry_point_single_model(self):
        spec = _make_spec("ep_model")

        def register_fn():
            return (spec, DummyAdapter)

        mock_ep = MagicMock()
        mock_ep.name = "ep_model"
        mock_ep.load.return_value = register_fn

        with patch.object(
            importlib.metadata,
            "entry_points",
            return_value={"pantheon.scfm": [mock_ep]},
        ):
            registry = _fresh_registry()

        assert registry.get("ep_model") is spec
        assert registry.get_adapter_class("ep_model") is DummyAdapter

    def test_entry_point_multiple_models(self):
        spec_a = _make_spec("ep_a")
        spec_b = _make_spec("ep_b")

        class AdapterA(DummyAdapter):
            pass

        class AdapterB(DummyAdapter):
            pass

        def register_fn():
            return [(spec_a, AdapterA), (spec_b, AdapterB)]

        mock_ep = MagicMock()
        mock_ep.name = "multi"
        mock_ep.load.return_value = register_fn

        with patch.object(
            importlib.metadata,
            "entry_points",
            return_value={"pantheon.scfm": [mock_ep]},
        ):
            registry = _fresh_registry()

        assert registry.get("ep_a") is spec_a
        assert registry.get("ep_b") is spec_b
        assert registry.get_adapter_class("ep_a") is AdapterA
        assert registry.get_adapter_class("ep_b") is AdapterB

    def test_entry_point_bad_return_type_skipped(self):
        def register_fn():
            return "not a tuple"

        mock_ep = MagicMock()
        mock_ep.name = "bad"
        mock_ep.load.return_value = register_fn

        with patch.object(
            importlib.metadata,
            "entry_points",
            return_value={"pantheon.scfm": [mock_ep]},
        ):
            registry = _fresh_registry()

        # Should not crash; "bad" model should not exist
        assert registry.get("bad") is None

    def test_entry_point_load_exception_skipped(self):
        mock_ep = MagicMock()
        mock_ep.name = "crasher"
        mock_ep.load.side_effect = ImportError("missing dep")

        with patch.object(
            importlib.metadata,
            "entry_points",
            return_value={"pantheon.scfm": [mock_ep]},
        ):
            registry = _fresh_registry()

        assert registry.get("crasher") is None


# ---------------------------------------------------------------------------
# Local directory plugin loading
# ---------------------------------------------------------------------------

class TestLocalPluginDiscovery:
    """Test _discover_local_plugins with temp directory."""

    def test_local_plugin_loaded(self, tmp_path, monkeypatch):
        plugin_dir = tmp_path / ".pantheon" / "plugins" / "scfm"
        plugin_dir.mkdir(parents=True)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        plugin_code = textwrap.dedent("""\
            from pantheon.toolsets.scfm.registry import (
                ModelSpec, TaskType, Modality, GeneIDScheme,
                SkillReadyStatus, HardwareRequirements, OutputKeys,
            )
            from pantheon.toolsets.scfm.adapters.base import BaseAdapter

            SPEC = ModelSpec(
                name="local_test",
                version="0.1.0",
                skill_ready=SkillReadyStatus.PARTIAL,
                tasks=[TaskType.EMBED],
                modalities=[Modality.RNA],
                species=["human"],
                gene_id_scheme=GeneIDScheme.SYMBOL,
                zero_shot_embedding=True,
                output_keys=OutputKeys(embedding_key="X_local_test"),
                embedding_dim=128,
                hardware=HardwareRequirements(gpu_required=False, min_vram_gb=0, cpu_fallback=True),
            )

            class LocalTestAdapter(BaseAdapter):
                def __init__(self, checkpoint_dir=None):
                    super().__init__(SPEC, checkpoint_dir)
                def run(self, task, adata_path, output_path, **kw):
                    return {"status": "ok"}
                def _load_model(self, device):
                    pass
                def _preprocess(self, adata, task):
                    pass
                def _postprocess(self, adata, embeddings, task):
                    return []

            def register():
                return (SPEC, LocalTestAdapter)
        """)
        (plugin_dir / "my_local_model.py").write_text(plugin_code)

        registry = _fresh_registry()

        assert registry.get("local_test") is not None
        assert registry.get("local_test").name == "local_test"
        adapter_cls = registry.get_adapter_class("local_test")
        assert adapter_cls is not None
        assert adapter_cls.__name__ == "LocalTestAdapter"

    def test_local_plugin_no_register_skipped(self, tmp_path, monkeypatch):
        plugin_dir = tmp_path / ".pantheon" / "plugins" / "scfm"
        plugin_dir.mkdir(parents=True)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        (plugin_dir / "no_register.py").write_text("x = 42\n")

        registry = _fresh_registry()
        # Should not crash; no model named "no_register" or "x"
        assert registry.get("no_register") is None

    def test_local_plugin_underscore_skipped(self, tmp_path, monkeypatch):
        plugin_dir = tmp_path / ".pantheon" / "plugins" / "scfm"
        plugin_dir.mkdir(parents=True)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        (plugin_dir / "_helper.py").write_text(
            "def register(): raise RuntimeError('should not be called')\n"
        )

        # Should not crash
        registry = _fresh_registry()
        assert registry is not None

    def test_local_plugin_syntax_error_skipped(self, tmp_path, monkeypatch):
        plugin_dir = tmp_path / ".pantheon" / "plugins" / "scfm"
        plugin_dir.mkdir(parents=True)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

        (plugin_dir / "broken.py").write_text("def register(:\n")

        # Should not crash
        registry = _fresh_registry()
        assert registry is not None

    def test_no_plugin_dir_is_fine(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        # No .pantheon/plugins/scfm dir exists
        registry = _fresh_registry()
        assert len(registry.list_models()) >= 3


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestValidation:
    """Test _validate_and_register error handling."""

    def test_non_model_spec_rejected(self):
        registry = _fresh_registry()
        count_before = len(registry.list_models())
        registry._validate_and_register(
            {"name": "fake"}, DummyAdapter, source="test"
        )
        assert len(registry.list_models()) == count_before

    def test_non_base_adapter_rejected(self):
        registry = _fresh_registry()
        spec = _make_spec("bad_adapter_model")

        class NotAnAdapter:
            pass

        count_before = len(registry.list_models())
        registry._validate_and_register(spec, NotAnAdapter, source="test")
        assert len(registry.list_models()) == count_before

    def test_valid_plugin_accepted(self):
        registry = _fresh_registry()
        spec = _make_spec("good_model")
        count_before = len(registry.list_models())
        registry._validate_and_register(spec, DummyAdapter, source="test")
        assert len(registry.list_models()) == count_before + 1
        assert registry.get("good_model") is spec
