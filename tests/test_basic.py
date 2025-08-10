"""Basic test to verify pytest setup."""


def test_import():
    """Test that we can import socialmapper."""
    import socialmapper

    assert socialmapper is not None


def test_version():
    """Test that version is available."""
    import socialmapper

    assert hasattr(socialmapper, "__version__")
    assert isinstance(socialmapper.__version__, str)
