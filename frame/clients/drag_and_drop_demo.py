import gi
import sys

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf

(EXCHANGE_TYPE_NONE, EXCHANGE_TYPE_TEXT, EXCHANGE_TYPE_PIXBUF) = range(3)
(TARGET_ENTRY_TEXT, TARGET_ENTRY_PIXBUF) = range(2)
(COLUMN_TEXT, COLUMN_PIXBUF) = range(2)

DRAG_ACTION = Gdk.DragAction.COPY


class DragDropWindow(Gtk.Window):
    def __init__(self, source_mode, target_mode, expect):
        super().__init__(title="Drag and Drop Demo")
        self.fullscreen()

        drop_area = DropArea(target_mode, self.result_callback)
        iconview = DragSourceIconView(source_mode)

        sourcebox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        if source_mode == EXCHANGE_TYPE_NONE:
            sourcebox.pack_start(iconview.buttons(), False, False, 0)
        sourcebox.pack_start(iconview, True, True, 0)

        dropbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        if target_mode == EXCHANGE_TYPE_NONE:
            dropbox.pack_start(drop_area.buttons(), False, False, 0)
        dropbox.pack_start(drop_area, True, True, 0)
        dropbox.pack_start(drop_area.feedback, False, True, 0)
        if expect != EXCHANGE_TYPE_NONE:
            self.expect = expect
            self.result = EXCHANGE_TYPE_NONE
        else:
            self.expect = EXCHANGE_TYPE_NONE
            self.result = EXCHANGE_TYPE_NONE

        hbox = Gtk.Box(spacing=12)
        hbox.pack_start(sourcebox, False, True, 0)
        hbox.pack_start(dropbox, True, True, 0)
        self.add(hbox)

    def result_callback(self, result):
        self.result = result
        if self.expect != EXCHANGE_TYPE_NONE:
            print("expect=", self.expect, ", actual=", self.result)
            exit(self.result != self.expect)

class DragSourceIconView(Gtk.IconView):
    def __init__(self, source_mode):
        Gtk.IconView.__init__(self)
        self.set_text_column(COLUMN_TEXT)
        self.set_pixbuf_column(COLUMN_PIXBUF)

        model = Gtk.ListStore(str, GdkPixbuf.Pixbuf)
        self.set_model(model)
        self.add_item("Item 1", "image-missing")
        self.add_item("Item 2", "help-about")
        self.add_item("Item 3", "edit-copy")

        self.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK, [], DRAG_ACTION)
        self.connect("drag-data-get", self.on_drag_data_get)

        if source_mode == EXCHANGE_TYPE_TEXT:
            self.set_text_targets()
        elif source_mode == EXCHANGE_TYPE_PIXBUF:
            self.set_image_targets()

    def buttons(self):
        self.set_image_targets();
        image_button = Gtk.RadioButton.new_with_label_from_widget(None, "Images")
        image_button.connect("toggled", self.set_image_targets)
        text_button = Gtk.RadioButton.new_with_label_from_widget(image_button, "Text")
        text_button.connect("toggled", self.set_text_targets)
        both_button = Gtk.RadioButton.new_with_label_from_widget(image_button, "Both")
        text_button.connect("toggled", self.set_both_targets)
        button_box = Gtk.Box(spacing=6)
        button_box.pack_start(image_button, False, False, 0)
        button_box.pack_start(text_button, False, False, 0)
        button_box.pack_start(both_button, False, False, 0)
        return button_box

    def set_image_targets(self, button=None):
        targets = Gtk.TargetList.new(None)
        targets.add_image_targets(TARGET_ENTRY_PIXBUF, True)
        self.drag_source_set_target_list(targets)

    def set_text_targets(self, button=None):
        targets = Gtk.TargetList.new(None)
        targets.add_text_targets(TARGET_ENTRY_TEXT)
        self.drag_source_set_target_list(targets)

    def set_both_targets(self, button=None):
        targets = Gtk.TargetList.new(None)
        targets.add_image_targets(TARGET_ENTRY_PIXBUF, True)
        targets.add_text_targets(TARGET_ENTRY_TEXT)
        self.drag_source_set_target_list(targets)

    def on_drag_data_get(self, widget, drag_context, data, info, time):
        selected_path = self.get_selected_items()[0]
        selected_iter = self.get_model().get_iter(selected_path)

        if info == TARGET_ENTRY_TEXT:
            text = self.get_model().get_value(selected_iter, COLUMN_TEXT)
            data.set_text(text, -1)
        elif info == TARGET_ENTRY_PIXBUF:
            pixbuf = self.get_model().get_value(selected_iter, COLUMN_PIXBUF)
            data.set_pixbuf(pixbuf)

    def add_item(self, text, icon_name):
        try:
            pixbuf = Gtk.IconTheme.get_default().load_icon(icon_name, 16, 0)
        except:
            pixbuf = Gtk.IconTheme.get_default().load_icon(icon_name + "-symbolic", 16, 0)

        self.get_model().append([text, pixbuf])


class DropArea(Gtk.Label):
    def __init__(self, target_mode, result_callback):
        Gtk.Label.__init__(self)
        self.feedback = Gtk.Label.new()
        self.feedback.set_label("(nothing)")
        self.result_callback = result_callback

        self.set_label("Drop something on me!")
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], DRAG_ACTION)

        self.connect("drag-data-received", self.on_drag_data_received)
        self.connect("drag-motion", self.on_drag_motion)
        self.connect("drag-leave", self.on_drag_leave)

        if target_mode:
            if target_mode == EXCHANGE_TYPE_TEXT:
                self.set_text_targets()
            if target_mode == EXCHANGE_TYPE_PIXBUF:
                self.set_image_targets()

    def buttons(self):
        self.set_image_targets()
        image_button = Gtk.RadioButton.new_with_label_from_widget(None, "Images")
        image_button.connect("toggled", self.set_image_targets)
        text_button = Gtk.RadioButton.new_with_label_from_widget(image_button, "Text")
        text_button.connect("toggled", self.set_text_targets)
        button_box = Gtk.Box(spacing=6)
        button_box.pack_start(image_button, False, False, 0)
        button_box.pack_start(text_button, False, False, 0)
        return button_box

    def set_image_targets(self, button=None):
        targets = Gtk.TargetList.new(None)
        targets.add_image_targets(TARGET_ENTRY_PIXBUF, True)
        self.drag_dest_set_target_list(targets)

    def set_text_targets(self, button=None):
        targets = Gtk.TargetList.new(None)
        targets.add_text_targets(TARGET_ENTRY_TEXT)
        self.drag_dest_set_target_list(targets)

    def on_drag_motion(self, widget, drag_context, x, y, time):
        actions = drag_context.get_actions().value_names
        targets = [str(target) for target in drag_context.list_targets()]
        self.feedback.set_label("Actions: %s, offers: %s" % (actions, targets))
        return False

    def on_drag_leave(self, widget, drag_context, time):
        self.feedback.set_label("(leave)")
        return False

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        if info == TARGET_ENTRY_TEXT:
            self.result_callback(EXCHANGE_TYPE_TEXT)
            text = data.get_text()
            self.feedback.set_label("Received text: %s" % text)
        elif info == TARGET_ENTRY_PIXBUF:
            self.result_callback(EXCHANGE_TYPE_PIXBUF)
            pixbuf = data.get_pixbuf()
            width = pixbuf.get_width()
            height = pixbuf.get_height()
            self.feedback.set_label("Received pixbuf with width %spx and height %spx" % (width, height))

def exchange_type(text):
    match text:
        case "text": return EXCHANGE_TYPE_TEXT
        case "pixbuf": return EXCHANGE_TYPE_PIXBUF
        case _: raise TypeError('Unknown exchange type: "%s"' % text)

if __name__ == '__main__':
    source_mode=EXCHANGE_TYPE_NONE
    target_mode=EXCHANGE_TYPE_NONE
    expect=EXCHANGE_TYPE_NONE
    try:
        args = sys.argv[1:] or []
        commands: list = []
        while args:
            arg = args.pop(0)
            if arg == '--source':
                source_mode = exchange_type(args.pop(0))
            elif arg == '--target':
                target_mode = exchange_type(args.pop(0))
            elif arg == '--expect':
                expect = exchange_type(args.pop(0))
            else:
                assert False, f'invalid argument: {arg}'
    except Exception as e:
        print('Argument error:', str(e))
        exit(1)
    win = DragDropWindow(source_mode=source_mode, target_mode=target_mode, expect=expect)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
    if expect != EXCHANGE_TYPE_NONE:
        exit(win.result != expect)
