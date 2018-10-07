# -*- coding: utf-8 -*-
import pytest

from chaosk8s_wix import __version__, discover


def test_discover_extension_capabilities():
    discovery = discover(discover_system=False)
    assert discovery["extension"]["name"] == "chaostoolkit-k8s-wix"
    assert discovery["extension"]["version"] == __version__
    assert len(discovery["activities"]) > 0
