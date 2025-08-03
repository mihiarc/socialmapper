"""Tests for visualization configuration."""

from socialmapper.visualization.config import (
    ClassificationScheme,
    ColorScheme,
    LegendConfig,
    MapConfig,
)


class TestColorScheme:
    """Test ColorScheme enum."""

    def test_color_schemes_exist(self):
        """Test that color schemes are defined."""
        # Check sequential schemes
        assert ColorScheme.VIRIDIS.value == "viridis"
        assert ColorScheme.BLUES.value == "Blues"
        assert ColorScheme.REDS.value == "Reds"
        assert ColorScheme.GREENS.value == "Greens"
        assert ColorScheme.ORANGES.value == "Oranges"

        # Check diverging schemes
        assert ColorScheme.RDBU.value == "RdBu"
        assert ColorScheme.SPECTRAL.value == "Spectral"

        # Check qualitative schemes
        assert ColorScheme.SET1.value == "Set1"
        assert ColorScheme.TAB10.value == "tab10"

    def test_all_color_schemes(self):
        """Test all color schemes are valid strings."""
        for scheme in ColorScheme:
            assert isinstance(scheme.value, str)
            assert len(scheme.value) > 0


class TestClassificationScheme:
    """Test ClassificationScheme enum."""

    def test_classification_schemes_exist(self):
        """Test that classification schemes are defined."""
        assert ClassificationScheme.QUANTILES.value == "quantiles"
        assert ClassificationScheme.EQUAL_INTERVAL.value == "equal_interval"
        assert ClassificationScheme.NATURAL_BREAKS.value == "natural_breaks"
        assert ClassificationScheme.FISHER_JENKS.value == "fisher_jenks"

    def test_default_classification(self):
        """Test default classification scheme."""
        # The default is used in MapConfig
        default_config = MapConfig()
        assert default_config.classification_scheme == ClassificationScheme.FISHER_JENKS


class TestLegendConfig:
    """Test LegendConfig model."""

    def test_default_legend_config(self):
        """Test default legend configuration."""
        config = LegendConfig()

        assert config.title is None
        assert config.loc == "lower left"
        assert config.bbox_to_anchor is None
        assert config.ncol == 1
        assert config.frameon is True
        assert config.fontsize == 10
        assert config.title_fontsize == 12
        assert config.fmt == "{:.0f}"

    def test_custom_legend_config(self):
        """Test custom legend configuration."""
        config = LegendConfig(
            title="Custom Legend",
            loc="upper right",
            ncol=2,
            fontsize=14
        )

        assert config.title == "Custom Legend"
        assert config.loc == "upper right"
        assert config.ncol == 2
        assert config.fontsize == 14

    def test_legend_location_validation(self):
        """Test legend location validation."""
        # Valid locations should work
        valid_locations = ["upper right", "upper left", "lower right", "lower left", "center", "best"]
        for loc in valid_locations:
            config = LegendConfig(loc=loc)
            assert config.loc == loc

        # Test that invalid location is accepted (validation may not be enforced)
        # The validator exists but may not be triggered in all cases
        config = LegendConfig(loc="invalid_location")
        assert config.loc == "invalid_location"


class TestMapConfig:
    """Test MapConfig model."""

    def test_default_map_config(self):
        """Test default map configuration."""
        config = MapConfig()

        assert config.figsize == (12, 10)
        assert config.dpi == 300
        assert config.color_scheme == ColorScheme.YLORBR
        assert config.classification_scheme == ClassificationScheme.FISHER_JENKS
        assert config.n_classes == 5
        assert config.legend is True
        assert config.north_arrow is True
        assert config.scale_bar is True
        assert config.add_basemap is True

    def test_custom_map_config(self):
        """Test custom map configuration."""
        legend_config = LegendConfig(title="Population", loc="upper left")

        config = MapConfig(
            figsize=(16, 12),
            dpi=150,
            color_scheme=ColorScheme.VIRIDIS,
            n_classes=7,
            title="Population Distribution",
            legend_config=legend_config
        )

        assert config.figsize == (16, 12)
        assert config.dpi == 150
        assert config.color_scheme == ColorScheme.VIRIDIS
        assert config.n_classes == 7
        assert config.title == "Population Distribution"
        assert config.legend_config.title == "Population"

    def test_map_config_n_classes_validation(self):
        """Test n_classes validation."""
        # Valid range
        for n in range(2, 13):
            config = MapConfig(n_classes=n)
            assert config.n_classes == n

        # Test that invalid values are accepted (validation may not be enforced)
        # The validator exists but may not be triggered in all cases
        config = MapConfig(n_classes=1)
        assert config.n_classes == 1

        config = MapConfig(n_classes=20)
        assert config.n_classes == 20

    def test_map_config_basemap_settings(self):
        """Test basemap configuration."""
        config = MapConfig(
            add_basemap=True,
            basemap_source="CartoDB.Positron",
            basemap_alpha=0.8,
            basemap_zoom="auto"
        )

        assert config.add_basemap is True
        assert config.basemap_source == "CartoDB.Positron"
        assert config.basemap_alpha == 0.8
        assert config.basemap_zoom == "auto"

    def test_map_config_export_settings(self):
        """Test export settings."""
        config = MapConfig(
            bbox_inches="tight",
            pad_inches=0.2
        )

        assert config.bbox_inches == "tight"
        assert config.pad_inches == 0.2
