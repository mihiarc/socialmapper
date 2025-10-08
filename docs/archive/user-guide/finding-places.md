# Finding Places

SocialMapper can find various types of community resources using OpenStreetMap data. This guide shows you how to search for different places.

## Common Place Types

### Essential Services

**Libraries**
```python
run_socialmapper(
    state="Illinois",
    county="Cook County",
    place_type="library",
    travel_time=15
)
```

**Schools**
```python
run_socialmapper(
    state="Texas",
    county="Harris County",
    place_type="school",
    travel_time=10
)
```

**Hospitals**
```python
run_socialmapper(
    state="California",
    county="Los Angeles County",
    place_type="hospital",
    travel_time=20
)
```

### Community Resources

**Parks**
```python
run_socialmapper(
    state="Colorado",
    county="Denver County",
    place_type="park",
    travel_time=15
)
```

**Grocery Stores**
```python
run_socialmapper(
    state="Ohio",
    county="Franklin County",
    place_type="supermarket",
    travel_time=10
)
```

**Community Centers**
```python
run_socialmapper(
    state="Washington",
    county="King County",
    place_type="community_centre",
    travel_time=15
)
```

## OpenStreetMap Tags

SocialMapper uses OpenStreetMap tags to find places. Common tags include:

### Amenity Tags
- `library` - Public libraries
- `school` - Schools (all levels)
- `hospital` - Hospitals
- `clinic` - Medical clinics
- `pharmacy` - Pharmacies
- `bank` - Banks
- `post_office` - Post offices
- `police` - Police stations
- `fire_station` - Fire stations
- `community_centre` - Community centers

### Shop Tags
- `supermarket` - Grocery stores
- `convenience` - Convenience stores
- `bakery` - Bakeries
- `butcher` - Butcher shops

### Leisure Tags
- `park` - Parks
- `playground` - Playgrounds
- `sports_centre` - Sports facilities
- `swimming_pool` - Public pools

## Advanced Searches

### Using POI Type and Name

For more specific searches, combine type and name:

```python
# Find all Whole Foods locations
run_socialmapper(
    state="California",
    county="Orange County",
    poi_type="shop",
    poi_name="supermarket",
    travel_time=15
)
```

### Multiple Counties

Analyze multiple counties at once:

```python
# Analyze libraries across a metro area
for county in ["Cook County", "DuPage County", "Lake County"]:
    results = run_socialmapper(
        state="Illinois",
        county=county,
        place_type="library",
        travel_time=15
    )
```

## Tips for Finding Places

1. **Use singular forms** - `library` not `libraries`
2. **Check OpenStreetMap** - Visit openstreetmap.org to verify place names
3. **Try variations** - Some places might be tagged differently
4. **Be specific** - Use exact county names with "County" suffix

## Command Line Examples

Find libraries:
```bash
socialmapper analyze --state "New York" --county "New York County" \
  --place-type "library" --travel-time 15
```

Find hospitals with custom output:
```bash
socialmapper analyze --state "Florida" --county "Miami-Dade County" \
  --place-type "hospital" --travel-time 20 --export-csv --export-maps
```

## Troubleshooting

**No places found?**
- Verify the county name is correct
- Check if the place type exists in that area
- Try a broader search area
- Ensure internet connection is active

**Too many results?**
- Use poi_name to filter further
- Reduce the geographic area
- Export to CSV and filter in Excel

## Next Steps

- Learn about [analyzing travel times](travel-time.md)
- Add [demographic analysis](demographics.md)
- Use [your own locations](custom-locations.md)