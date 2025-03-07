# compandkins
Apply dynamic compression/expansion to podcast mp3s, to make them listenable in a noisy environment.

There is also an option to remove gaps of silence, because I wanted to maximize content in my limited time.


# Installation
`pip install -r requirements.txt`

Change paths `pods` and `outdir` to your preferred directories. `pods` should contain **subdirectories** of each show, each containing episode MP3s.

Please look at the source to find more information about the silence-removal option,

# Caveats
- This script takes no arguments, command line options, nor config file.
- The source must be changed to suit individual cases.
- Images are lost in the conversion.
