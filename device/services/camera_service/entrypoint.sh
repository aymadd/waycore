#!/bin/sh
# Camera service entrypoint
# Copies sample photos to the data directory if they don't exist

# Ensure photos directory exists
mkdir -p /app/data/photos

# Copy sample photo if not already present (for gallery testing)
if [ -f /app/sample/IMG_20240101_120000_waycore.jpg ] && [ ! -f /app/data/photos/IMG_20240101_120000_waycore.jpg ]; then
    cp /app/sample/IMG_20240101_120000_waycore.jpg /app/data/photos/
    echo "Sample photo copied to /app/data/photos/"
fi

# Run the main service
exec python -m device.services.camera_service.main
