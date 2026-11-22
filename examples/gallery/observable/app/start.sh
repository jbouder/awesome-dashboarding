#!/bin/sh
# Build the site with fresh data, then serve it. Runs at every container start.
set -eu

# Drop cached data loader output so the build queries the warehouse again.
# Keep the npm cache that the image build filled.
rm -rf src/.observablehq/cache/data dist

echo "Building the site. The data loaders query the warehouse now."
npx observable build
exec node serve.js
