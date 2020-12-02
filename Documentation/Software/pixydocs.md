# Pixy Information
The PixyCam uses color signatures and color codes to find objects. Setting up color signatures and color codes will be documented by a helpful individual in the future. Once the PixyCam has desired signatures or codes, it will look for blocks of those colors in its field of vision. Color codes can be utilized as unique identifying codes. When the PixyCam finds a block of color, it gives us a structure including the signature (composed of the codes it found as the smallest numerical representation, ie if the codes it finds are 3, 5, and 1, the signature will appear as 153 instead of 351), the x position of the center of the signature, the y position of the center of the signature, the width of the signature in pixels, the height of the signature in pixels, the angle of the signature, the index, and the age.

## pixyController.py
Finds the bots' signatures and stores them in an array. Has functionality to return bots' IDs, positions, rotations, the size of signature, and the size of the frame that the pixy is viewing.
Utilizes functions from the Pixy python library.

### Notable functions:
`get_frame_dimensions_pixels(self)`

Returns the size of the frame of the pixy's field of view in pixels.


`get_frame_dimensions_units(self, h)`

Given the height h of the camera from the top of the bot, returns the size of the frame of the pixy's field of view in the same unit as h.


`get_all_bot_positions(self)`

Returns an array of structures of information about each detected bot, up to 10 bots.


`get_bot_position(self, signature)`

Given a color signature, returns a structure of information about the bot with that signature if detected, otherwise returns None.


`get_all_bot_angles(self)`

Returns an array of angles of detected bots.


`get_bot_angle(self, signature)`

Given a color signature, returns the angle of the bot with that signature if detected, otherwise returns None.
