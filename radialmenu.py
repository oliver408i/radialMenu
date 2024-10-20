import os
from Cocoa import (
    NSObject,
    NSApplication,
    NSApp,
    NSAlert,
    NSWindowStyleMaskBorderless,
    NSBackingStoreBuffered,
    NSColor,
    NSApplicationActivationPolicyAccessory,
    NSApplicationActivateAllWindows,
    NSScreen,
    NSStatusWindowLevel,
    NSCursor,
    NSStatusBar,
    NSMenu,
    NSMenuItem,
    NSApplicationPresentationHideDock,
    NSImage
)
from Foundation import NSUserDefaults, NSDictionary
from PyObjCTools import AppHelper
from shared import OverlayPanel, RadialMenuView
import Quartz

# Global variable to store reference to the AppDelegate
app_delegate = None
is_menu_open = False

defaults = NSUserDefaults.standardUserDefaults()
settings_dict = defaults.objectForKey_("RadialMenuSettings")

settings = None

if settings_dict is not None:
    settings = dict(settings_dict)
else:
    settings = {
        "hotkey": "Command+Shift+A",
        "menubarTitle": "RadialAS"
    }

def saveSettings():
    defaults = NSUserDefaults.standardUserDefaults()
    settings_dict = NSDictionary.dictionaryWithDictionary_(settings)
    defaults.setObject_forKey_(settings_dict, "RadialMenuSettings")
    defaults.synchronize()

def parseHotkey(hotkey_str):
    modifiers = 0
    key_code = None

    if "Command" in hotkey_str:
        modifiers |= Quartz.kCGEventFlagMaskCommand
    if "Shift" in hotkey_str:
        modifiers |= Quartz.kCGEventFlagMaskShift
    if "Option" in hotkey_str:
        modifiers |= Quartz.kCGEventFlagMaskAlternate
    if hotkey_str.endswith("A"):
        key_code = 0  # 'A' key
    elif hotkey_str.endswith("S"):
        key_code = 1  # 'S' key
    elif hotkey_str.endswith("R"):
        key_code = 15  # 'R' key

    return modifiers, key_code

def eventTapCallback(proxy, type_, event, refcon):
    global is_menu_open

    # Extract keycode and modifiers
    key_code = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
    modifiers = Quartz.CGEventGetFlags(event)

    # Parse hotkey from settings
    expected_modifiers, expected_key_code = parseHotkey(settings["hotkey"])

    if (
        type_ == Quartz.kCGEventKeyDown and
        modifiers & expected_modifiers == expected_modifiers and
        key_code == expected_key_code
    ):
        if type_ == Quartz.kCGEventKeyDown:
            # Call the showRadialMenu method of AppDelegate
            if app_delegate and not is_menu_open:
                #print("Global hotkey pressed!")
                is_menu_open = True
                AppHelper.callAfter(app_delegate.showRadialMenu)
            return None  # Consume the event
    elif type_ == Quartz.kCGEventKeyUp and is_menu_open:
        if app_delegate:
            #print("Global hotkey released!")
            is_menu_open = False
            AppHelper.callAfter(app_delegate.hideRadialMenu)
            return None

    return event  # Pass the event through to the next app

def setupGlobalKeybindListener():
    # Create an event tap to capture all key down events globally
    event_mask = (1 << Quartz.kCGEventKeyDown) | (1 << Quartz.kCGEventKeyUp)
    event_tap = Quartz.CGEventTapCreate(
        Quartz.kCGSessionEventTap,
        Quartz.kCGHeadInsertEventTap,
        Quartz.kCGEventTapOptionDefault,
        event_mask,
        eventTapCallback,
        None
    )

    if not event_tap:
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Failed to create event tap!")
        alert.setInformativeText_("If you haven't yet, enable Accessibility permissions in System Preferences for this app (to record global key presses)!")
        alert.addButtonWithTitle_("OK")
        alert.runModal()
        AppHelper.stopEventLoop()
        quit()

    # Create a run loop source and add it to the run loop
    run_loop_source = Quartz.CFMachPortCreateRunLoopSource(None, event_tap, 0)
    Quartz.CFRunLoopAddSource(Quartz.CFRunLoopGetCurrent(), run_loop_source, Quartz.kCFRunLoopCommonModes)
    Quartz.CGEventTapEnable(event_tap, True)

    #print("Global keybind listener set up.")
    return event_tap

class AppDelegate(NSObject):
    overlayWindow = None
    keybindActive = False
    eventTap = None

    def applicationDidFinishLaunching_(self, notification):
        NSApp.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        NSApp.setPresentationOptions_(NSApplicationPresentationHideDock)
        
        # Setup the global keybind listener using external function
        self.eventTap = setupGlobalKeybindListener()
        self.setupMenubarItem()

    def setupMenubarItem(self):
        # Create a status bar item with a menu
        status_bar = NSStatusBar.systemStatusBar()
        self.status_item = status_bar.statusItemWithLength_(-1)  # -1 for variable length
        self.updateMenubarTitle()

        # Create a menu with Settings and Quit options
        menu = NSMenu.alloc().init()
        settings_item = NSMenu.alloc().init()

        # Add Hotkey options
        hotkey_menu = NSMenu.alloc().initWithTitle_("Change Hotkey")
        hotkey_options = ["Command+Shift+A",  "Command+Option+A", "Command+Shift+S", "Command+Option+S", "Command+Shift+R", "Command+Option+R"]
        for hotkey in hotkey_options:
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                hotkey, "changeHotkey:", ""
            )
            item.setRepresentedObject_(hotkey)
            hotkey_menu.addItem_(item)
        hotkey_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Change Hotkey", None, "")
        menu.setSubmenu_forItem_(hotkey_menu, hotkey_item)
        menu.addItem_(hotkey_item)

        # Add Menubar title options
        title_menu = NSMenu.alloc().initWithTitle_("Change Menubar Title")
        title_options = ["RadialAS", "RAS", "Circle", "Circle 2", "App icon"]
        for title in title_options:
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                title, "changeMenubarTitle:", ""
            )
            item.setRepresentedObject_(title)
            title_menu.addItem_(item)
        title_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Change Menubar Title", None, "")
        menu.setSubmenu_forItem_(title_menu, title_item)
        menu.addItem_(title_item)

        # Add Quit option
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit", "terminate:", ""
        )
        menu.addItem_(quit_item)

        self.status_item.setMenu_(menu)

    def updateMenubarTitle(self):
        title = settings["menubarTitle"]
        self.status_item.button().setImage_(None)
        if title == "RAS":
            self.status_item.button().setTitle_("RAS")
        elif title == "Circle":
            self.status_item.button().setTitle_("\u25CF")  # Unicode for a filled circle
        elif title == "Circle 2":
            self.status_item.button().setTitle_("\u29BE") 
        elif title == "RadialAS":
            self.status_item.button().setTitle_("RadialAS")
        else:
            icon = NSImage.alloc().initByReferencingFile_(os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Resources'), 'AppIcon.icns'))
            icon.setSize_((20, 20))
            self.status_item.button().setImage_(icon)
            self.status_item.button().setTitle_("")

        saveSettings()

    def changeHotkey_(self, sender):
        new_hotkey = sender.representedObject()
        settings["hotkey"] = new_hotkey
        #print(f"Hotkey changed to: {new_hotkey}")
        saveSettings()

    def changeMenubarTitle_(self, sender):
        new_title = sender.representedObject()
        settings["menubarTitle"] = new_title
        self.updateMenubarTitle()
        #print(f"Menubar title changed to: {new_title}")

    def showRadialMenu(self):
        try:
            #print("Showing radial menu")
            screenFrame = NSScreen.mainScreen().frame()
            self.overlayWindow = OverlayPanel.alloc().initWithContentRect_styleMask_backing_defer_(
                screenFrame,
                NSWindowStyleMaskBorderless,
                NSBackingStoreBuffered,
                False,
            )
            self.overlayWindow.setLevel_(NSStatusWindowLevel)
            self.overlayWindow.setOpaque_(False)
            self.overlayWindow.setBackgroundColor_(NSColor.clearColor())

            contentView = RadialMenuView.alloc().initWithFrame_(screenFrame)
            self.overlayWindow.setContentView_(contentView)

            NSApp.activateIgnoringOtherApps_(True)

            self.overlayWindow.makeKeyAndOrderFront_(None)
            self.overlayWindow.becomeKeyWindow()
            self.overlayWindow.makeFirstResponder_(contentView)
            NSCursor.hide()
        except Exception as e:
            #print("Exception in showRadialMenu:", e)
            pass

    def hideRadialMenu(self):
        #print("Hiding radial menu")
        if self.overlayWindow:
            selectedApp = self.overlayWindow.contentView().selectedApp
            if selectedApp:
                selectedApp.activateWithOptions_(NSApplicationActivateAllWindows)
            self.overlayWindow.orderOut_(None)
            self.overlayWindow = None

            NSCursor.unhide()

    def applicationWillTerminate_(self, notification):
        if self.eventTap:
            Quartz.CFMachPortInvalidate(self.eventTap)
            self.eventTap = None
        #print("Event tap removed.")

if __name__ == "__main__":
    app = NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    # Store reference to the app delegate globally
    app_delegate = delegate
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()
