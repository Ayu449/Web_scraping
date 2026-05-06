#!/usr/bin/env bash
cd "$(dirname "$0")"

for d in delta_velocity alifcloud paypal education_dynamics yash_technologies; do
    echo "Running $d..."
    cd "$d"
    python "${d}_scraper.py"
    cd ..
done

echo "Done."
