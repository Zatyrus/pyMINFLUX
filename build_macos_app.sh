# To build, use the following command: currently there appears to be an issue with pyqtgraph
pyinstaller pyminflux/main.py \
--hidden-import="sklearn.metrics._pairwise_distances_reduction._datasets_pair" \
--hidden-import="sklearn.metrics._pairwise_distances_reduction._middle_term_computer" \
--noconsole \
--icon pyminflux/ui/assets/Logo_v3.icns \
--name pyminflux \
--noconfirm
