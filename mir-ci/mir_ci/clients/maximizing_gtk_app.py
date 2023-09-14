import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk
from gi.repository import GLib

def on_activate(app):
    window = Gtk.ApplicationWindow(application=app)
    button = Gtk.Button(label="Hello, World!")
    button.connect('clicked', lambda x: window.close())
    window.set_child(button)
    window.set_default_size(500, 300)
    window.present()
    # Doing this immediately keeps the window from being resized when it's restored
    GLib.timeout_add(500, lambda: window.maximize())

app = Gtk.Application(application_id='io.mir-server.test-gtk-app')
app.connect('activate', on_activate)
app.run(None)
