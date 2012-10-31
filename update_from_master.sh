#!/bin/bash

cp $0 ..
git rm -rf .
git commit -m "Removed old docs"
git checkout master
cd docs
make html
cp -r _build/html ..
git checkout .
cd ..
git checkout gh-pages
mv html/* .
rm -rf html
git add .
git commit -m "Added new docs"
cp ../$0 .
./prepare_for_github.sh
