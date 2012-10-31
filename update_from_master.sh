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
git add $0
git commit -m "Re-added update script"

# Prepare the files for github...
for fl in `find . -name "*.html"` `find . -name "*.txt"` `find . -name "*.svg"` `find . -name "*.js"` `find . -name "*.css"`
do
  echo "Processing $fl"
  mv $fl $fl.old
  sed 's/_images/images/g' $fl.old > $fl
  mv $fl $fl.old
  sed 's/_modules/modules/g' $fl.old > $fl
  mv $fl $fl.old
  sed 's/_static/static/g' $fl.old > $fl
  mv $fl $fl.old
  sed 's/_sources/sources/g' $fl.old > $fl
  rm -f $fl.old
done
git mv _images images
git mv _modules modules
git mv _sources sources
git mv _static static

git add -u .

git commit -m "Prepared html files for output on github pages, which doesn't allow directories that begin with underscores."

