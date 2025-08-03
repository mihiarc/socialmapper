"""Tests for geocoding engine."""


from socialmapper.geocoding.engine import AddressGeocodingEngine
from socialmapper.geocoding.models import AddressProvider, GeocodingConfig


class TestAddressGeocodingEngine:
    """Test AddressGeocodingEngine class."""

    def test_engine_initialization(self):
        """Test engine initialization with default config."""
        engine = AddressGeocodingEngine()

        assert engine.config is not None
        assert isinstance(engine.config, GeocodingConfig)

    def test_engine_with_custom_config(self):
        """Test engine initialization with custom config."""
        config = GeocodingConfig(
            primary_provider=AddressProvider.GOOGLE,
            enable_cache=False,
            max_retries=5
        )

        engine = AddressGeocodingEngine(config)

        assert engine.config == config
        assert engine.config.primary_provider == AddressProvider.GOOGLE
        assert engine.config.enable_cache is False

    def test_has_required_methods(self):
        """Test that engine has required public methods."""
        engine = AddressGeocodingEngine()

        # Check required methods exist
        assert hasattr(engine, 'geocode_address')
        assert hasattr(engine, 'geocode_addresses_batch')
        assert hasattr(engine, 'get_statistics')

        # Check they are callable
        assert callable(engine.geocode_address)
        assert callable(engine.geocode_addresses_batch)
        assert callable(engine.get_statistics)
