#!/usr/bin/env python3
"""Simple test to see if rumps works."""

import rumps

class TestApp(rumps.App):
    def __init__(self):
        super(TestApp, self).__init__("Test", quit_button='Quit')
        self.menu = ["Click Me"]

    @rumps.clicked("Click Me")
    def clicked(self, _):
        rumps.alert("It works!")

if __name__ == "__main__":
    print("Starting test app...")
    print("Look for 'Test' in your menu bar")
    TestApp().run()
