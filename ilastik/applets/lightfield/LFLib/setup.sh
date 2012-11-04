cd ImageProcessing/
python setup.py build_ext --inplace
cd ./../LFDepth
python setup.py build_ext --inplace
cd ./../Viewer
pyuic4 viewer.ui > viewerUI.py
pyuic4 previewer.ui > previewerUI.py

cp viewer.py viewLF
chmod +x viewLF

sudo cp viewLF /usr/bin/viewLF
