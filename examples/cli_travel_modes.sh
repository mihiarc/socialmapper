#!/bin/bash
# Example script showing how to use different travel modes with the SocialMapper CLI

echo "=== SocialMapper CLI Travel Mode Examples ==="
echo

# Example 1: Walking to parks (15 minutes)
echo "1. Finding parks within 15-minute walk in Chapel Hill, NC"
socialmapper --poi \
    --geocode-area "Chapel Hill" \
    --state "NC" \
    --poi-type "leisure" \
    --poi-name "park" \
    --travel-time 15 \
    --travel-mode walk \
    --census-variables total_population median_age \
    --output-dir output/cli_walk_example

echo
echo "2. Finding libraries within 10-minute bike ride in Chapel Hill, NC"
socialmapper --poi \
    --geocode-area "Chapel Hill" \
    --state "NC" \
    --poi-type "amenity" \
    --poi-name "library" \
    --travel-time 10 \
    --travel-mode bike \
    --census-variables total_population median_household_income \
    --output-dir output/cli_bike_example

echo
echo "3. Finding hospitals within 20-minute drive in Chapel Hill, NC"
socialmapper --poi \
    --geocode-area "Chapel Hill" \
    --state "NC" \
    --poi-type "amenity" \
    --poi-name "hospital" \
    --travel-time 20 \
    --travel-mode drive \
    --census-variables total_population percent_over_65 \
    --output-dir output/cli_drive_example

echo
echo "4. Using custom coordinates with bike mode"
# First create a sample CSV file
cat > output/sample_locations.csv << EOF
name,lat,lon
UNC Campus,35.9049,-79.0482
Franklin Street,35.9132,-79.0558
Carrboro Plaza,35.9101,-79.0753
EOF

socialmapper \
    --custom-coords output/sample_locations.csv \
    --travel-time 15 \
    --travel-mode bike \
    --census-variables total_population median_age \
    --output-dir output/cli_custom_bike_example

echo
echo "=== Examples Complete ==="
echo "Check the output folders to see how different travel modes create different isochrone shapes!"