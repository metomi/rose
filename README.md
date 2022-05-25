(Github Pages Branch Readme)

# How to deploy:

```
# Change into workflow
cd /path/to/rose/sphinx

# Make the documentation
make clean html

# Checkout the gh-pages branch in a new worktree
git worktree add ../../rose-doc
cd ../../rose-doc
git co upstream/gh-pages
git co --branch "<Sensible branch name>"

# Copy documentation to this branch
cp -r ../rose/doc/rose\ x.x.x x.x.x

# Add version folder
edit versions.json

# Test that it works
python -m http.server
```

You can then commit your changes, push your branch and create a PR.
