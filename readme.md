# Turtle3D

![Turtle3D Showcase GIF](https://i.ibb.co/xhMQTJ3/gif.gif)

A 3D engine in Turtle, because why not?

## Features

- A scene system that is similar to modern game engines (a lot simpler of course)
- A physical camera system, with gimbal lock prevention features
- A robust object system, with full transformation support and vertex management
- Lighting/Material framework allowing for physical light objects and materials applied to objects (experimental)
- Loading OBJ files directly
- Realtime positioning in 3D space using vectors

## Potential Improvements

- A raycasted lighting system with shadows
- Proper object clipping management
- Parent/child system for objects alongside object groups
- Improved turtle management/optimisation
- Verifying function parameters and proper documentation (beyond docstrings)
- Vector3 classes instead of lists
- A lot more flexible vertex management/manipulation.

## Setup

1) Download/copy the `Turtle3D.py` script.
2) Ensure it is in the same directory as the script you wish to work in.
3) Import Turtle3D

## Usage

Turtle3D has a lot of methods to explicitly document, but every method has docstrings to help.

As a rule of thumb, methods and variables beginning with `_` mean they are used solely internally, and should not be used directly, and only in read-only situations.

For example, `Object` instances, have a `_position` variable, however instead of interfacing with it directly, the sub-method `set_position` or `translate` should be used. 

Other methods and variables are free to be used more often and interacted with directly.

Examples of how to use Turtle3D can be found in `demo.py`.

## Contributing and Licensing

![Turtle3D Showcase Cover](https://i.ibb.co/yn66X3t/cover.jpg)

Feel free to contribute by creating a pull request or forking the repository.

I recommend forking rather than iterating on this repo because I doubt I will be checking it often.

Before making any changes, please be aware that this code is licensed with the [GNU GPLv3](https://choosealicense.com/licenses/gpl-3.0/) and should be used accordingly.