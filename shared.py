from Cocoa import (
    NSPanel,
    NSView,
    NSWindowStyleMaskBorderless,
    NSPoint,
    NSMakeRect,
    NSColor,
    NSBezierPath,
    NSWorkspace,
    NSTrackingArea,
    NSTrackingMouseMoved,
    NSTrackingActiveAlways,
    NSTrackingInVisibleRect,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorTransient,
    NSWindowCollectionBehaviorIgnoresCycle,
    NSStatusWindowLevel,
    NSFont,
    NSMutableParagraphStyle,
    NSFontAttributeName,
    NSForegroundColorAttributeName,
    NSParagraphStyleAttributeName
)
import objc, math

class OverlayPanel(NSPanel):
    def initWithContentRect_styleMask_backing_defer_(self, rect, style, backing, defer):
        try:
            self = objc.super(OverlayPanel, self).initWithContentRect_styleMask_backing_defer_(
                rect,
                style,
                backing,
                defer,
            )
            if self:
                self.setOpaque_(False)
                self.setBackgroundColor_(NSColor.clearColor())
                self.setAlphaValue_(0.7)  # Set semi-transparency for the popup
                self.setLevel_(NSStatusWindowLevel)
                self.setIgnoresMouseEvents_(False)
                self.setCollectionBehavior_(
                    NSWindowCollectionBehaviorCanJoinAllSpaces
                    | NSWindowCollectionBehaviorTransient
                    | NSWindowCollectionBehaviorIgnoresCycle
                )
                self.setStyleMask_(NSWindowStyleMaskBorderless)
            return self
        except Exception as e:
            print("Exception in OverlayPanel init:", e)
            return None

    def canBecomeKeyWindow(self):
        return True

    def canBecomeMainWindow(self):
        return True

class RadialMenuView(NSView):
    selectedApp = None

    def isFlipped(self):
        return True

    def acceptsFirstResponder(self):
        return True

    def becomeFirstResponder(self):
        return True

    def resignFirstResponder(self):
        return True

    def initWithFrame_(self, frame):
        try:
            self = objc.super(RadialMenuView, self).initWithFrame_(frame)
            if self:
                self.apps = [
                    app
                    for app in NSWorkspace.sharedWorkspace().runningApplications()
                    if app.activationPolicy() == 0  # NSApplicationActivationPolicyRegular
                ]
                self.selectedApp = self.apps[0] if self.apps else None  # Set the default selected app to the first app
                self.trackingArea = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
                    self.bounds(),
                    NSTrackingMouseMoved
                    | NSTrackingActiveAlways
                    | NSTrackingInVisibleRect,
                    self,
                    None,
                )
                self.addTrackingArea_(self.trackingArea)
            return self
        except Exception as e:
            print("Exception in RadialMenuView init:", e)
            return None

    def drawRect_(self, rect):
        try:
            numApps = len(self.apps)
            if numApps == 0:
                return

            center = NSPoint(self.bounds().size.width / 2, self.bounds().size.height / 2)
            radius = min(self.bounds().size.width, self.bounds().size.height) / 3
            innerRadius = radius / 1.8  # Make the hole in the middle smaller to make slices wider
            sliceThickness = (radius - innerRadius)  # Make the app slices much wider

            # Fill the inner circle with a different color
            innerCirclePath = NSBezierPath.bezierPathWithOvalInRect_(
                NSMakeRect(
                    center.x - innerRadius,
                    center.y - innerRadius,
                    innerRadius * 2,
                    innerRadius * 2,
                )
            )
            NSColor.colorWithCalibratedWhite_alpha_(0.2, 0.6).set()  # Semi-transparent fill color
            innerCirclePath.fill()

            for i, app in enumerate(self.apps):
                startAngle = -90 + (360.0 / numApps) * i
                endAngle = -90 + (360.0 / numApps) * (i + 1)

                path = NSBezierPath.bezierPath()
                path.moveToPoint_(center)
                path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_(
                    center,
                    innerRadius + sliceThickness,
                    startAngle,
                    endAngle,
                    False,
                )
                path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_(
                    center,
                    innerRadius,
                    endAngle,
                    startAngle,
                    True,
                )
                path.closePath()

                if app == self.selectedApp:
                    NSColor.orangeColor().set()  # Set selected color to orange
                else:
                    NSColor.darkGrayColor().set()  # Set unselected color to dark grey

                path.fill()

                # Draw app icon
                icon = app.icon()
                if icon:
                    # Compute the position in the sector
                    angle = math.radians((startAngle + endAngle) / 2)
                    iconSize = 48  # Set icon size for wider slices
                    x = center.x + (innerRadius + sliceThickness / 2) * math.cos(angle) - iconSize / 2
                    y = center.y + (innerRadius + sliceThickness / 2) * math.sin(angle) - iconSize / 2
                    iconRect = NSMakeRect(x, y, iconSize, iconSize)
                    icon.drawInRect_(iconRect)

            # Draw selected app name in the center
            if self.selectedApp:
                appName = self.selectedApp.localizedName()
                if appName:
                    fontSize = 14  # Larger font size for better visibility
                    font = NSFont.systemFontOfSize_(fontSize)
                    paragraphStyle = NSMutableParagraphStyle.alloc().init()
                    paragraphStyle.setAlignment_(1)  # Center alignment

                    attributes = {
                        NSFontAttributeName: font,
                        NSParagraphStyleAttributeName: paragraphStyle,
                        NSForegroundColorAttributeName: NSColor.whiteColor()  # White text color
                    }

                    textWidth = innerRadius * 1.5  # Limit the width to avoid overflow
                    textRect = NSMakeRect(
                        center.x - textWidth / 2,
                        center.y - fontSize,  # Shift text upwards slightly to prevent cutoff
                        textWidth,
                        fontSize * 1.5,  # Increase height to prevent the bottom from being cut off
                    )

                    # Draw the app name in the centered text rect
                    appName.drawInRect_withAttributes_(textRect, attributes)

            # Calculate mouse location and angle
            mouseLocation = self.window().mouseLocationOutsideOfEventStream()
            dx = mouseLocation.x - center.x
            dy = mouseLocation.y - center.y

            arrowAngle = math.atan2(dy, dx)  # Calculate the correct arrow direction
            arrowAngle = -arrowAngle  # Flip the angle to match the coordinate system

            arrowLength = innerRadius * 0.8  # Adjust the length for the '>' symbol

            # Start drawing the '>' symbol as two lines converging at the tip
            arrowPath = NSBezierPath.bezierPath()

            # Define the tip point of the '>'
            tipPoint = NSPoint(
                center.x + arrowLength * math.cos(arrowAngle),
                center.y + arrowLength * math.sin(arrowAngle),
            )

            # First outer point (left side)
            leftOuterPoint = NSPoint(
                center.x + (arrowLength - 5) * math.cos(arrowAngle - 0.1),
                center.y + (arrowLength - 5) * math.sin(arrowAngle - 0.1),
            )

            # Second outer point (right side)
            rightOuterPoint = NSPoint(
                center.x + (arrowLength - 5) * math.cos(arrowAngle + 0.1),
                center.y + (arrowLength - 5) * math.sin(arrowAngle + 0.1),
            )

            # Draw the first line from the left outer point to the tip
            arrowPath.moveToPoint_(leftOuterPoint)
            arrowPath.lineToPoint_(tipPoint)

            # Draw the second line from the right outer point to the tip
            arrowPath.lineToPoint_(rightOuterPoint)

            # Set the stroke color and line width for the '>' symbol
            NSColor.whiteColor().set()  # Set the color to white
            arrowPath.setLineWidth_(3.0)  # Adjust the line width to make it look like a proper '>'
            arrowPath.stroke()



        except Exception as e:
            print("Exception in drawRect_:", e)


    def mouseMoved_(self, event):
        try:
            location = self.convertPoint_fromView_(event.locationInWindow(), None)
            center = NSPoint(self.bounds().size.width / 2, self.bounds().size.height / 2)
            dx = location.x - center.x
            dy = location.y - center.y

            angle = math.degrees(math.atan2(dy, dx))
            angle = (angle + 360) % 360  # Normalize angle to [0, 360)

            numApps = len(self.apps)
            sectorAngle = 360.0 / numApps
            index = int((angle + 90) % 360 // sectorAngle)
            if 0 <= index < numApps:
                if self.selectedApp != self.apps[index]:
                    self.selectedApp = self.apps[index]
                    self.setNeedsDisplay_(True)
            self.setNeedsDisplay_(True)  # Redraw to update the arrow position
        except Exception as e:
            print("Exception in mouseMoved_:", e)
    
    def keyDown_(self, event):
        pass

    def mouseUp_(self, event):
        pass