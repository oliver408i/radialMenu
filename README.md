# MacOS Radial App Switcher
This small python-based app implements an alternative to the command+tab linear app switcher built in to MacOS. Instead it offers a radial verion of the app switcher, heavily inspired by the Satisfactory video game's radial menus.
## Using
You can download the prebuilt app from the releases section, but I highly recommend building it yourself to avoid security and anti-virus issues (since it isn't signed).  
The app will request for accessibility permissions on first run (this is required for global keybinds to work). If your keybind isn't working, try setting the keybind again by using the menu bar text/icon.  
This doesn't replace the command+tab app switcher, instead it implements a completely different gui, trigger by holding command+shift+A (by default, can be changed in the menu bar). By holding the keybind, the gui will pop up, and you can move your mouse to select the app you want to switch to. Once you release the keybind, the app that you selected will be focused.
## Building
To build, you'll need any modern version of python (3.8+), `pyobj`, and `py2app`.  
Run `python3.12 setup.py py2app` (or whatever python command you use)  
You'll find the output `.app` file in the `dist` folder.
## Why Quartz Event Taps
Capturing key presses globally isn't something a normal app would need to do, and thus AppKit doesn't have a complete built-in way to doing so (except `NSEvent`, but that doesn't work as I explain later). Instead, I had to use lower-level `Quartz` apis to do this. Using the Event Tap feature as part of the Accessibility framework, I can capture various events from the OS, such as key presses and releases. Although this requires the additional permission, and is more complicated, it allows the app to consume the event (block the event from going to app below it), something that `NSEvent` isn't able to do.
## Other OSes?
No, this app was build using MacOS-specific APIs and methods, and I won't/can't write a version of this for another OS.