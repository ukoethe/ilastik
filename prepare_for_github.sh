#!/bin/bash
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

