#!/bin/sh

# Clone the repository and checkout the test branch
git clone --branch testbranch https://github.com/yourusername/yourrepository.git /app || \
(cd /app && git pull && git checkout testbranch)

# Run the Flask application
exec python /app/app.py