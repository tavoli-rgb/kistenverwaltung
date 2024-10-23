#!/bin/sh

# Clone the repository and checkout the test branch
git clone --branch test https://github.com/tavoli-rgb/kistenverwaltung.git /app || \
(cd /app && git pull && git checkout testbranch)

# Run the Flask application
exec python /app/app.py