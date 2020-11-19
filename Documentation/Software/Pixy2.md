# Compiling the Pixy Library

## On Ubuntu/Mint/Debian based Linux distributions

Follow the [official Pixy2 guide](https://docs.pixycam.com/wiki/doku.php?id=wiki:v2:building_libpixyusb_as_a_python_module_on_linux).

## On MacOS

Make sure you have [Homebrew](https://brew.sh/) installed, then run the command
```
brew install swig libusb gcc git
```
which includes most of the tools needed to build the library. You also need Xcode's command line tools, which are included with Xcode or can be installed separately via the command
```
xcode-select --install
```
Then, follow the rest of the [official Pixy2 guide](https://docs.pixycam.com/wiki/doku.php?id=wiki:v2:building_libpixyusb_as_a_python_module_on_linux) (skipping the install dependencies section).

## After Building

Once the library is compiled, several build files should appear in `[pixy repository]/build/python_demos`.  Copy `pixy.i`, `_pixy.so`, `swig.dat`, and `pixy.py` to your SwimmingSwarm folder.  Due to differences in Python installs and OS versions these files are not tracked in the git repository.

You should now be able to run Pixy-related SwimmingSwarm code!