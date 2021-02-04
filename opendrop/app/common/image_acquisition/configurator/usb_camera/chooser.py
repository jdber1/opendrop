from gi.repository import Gtk, GObject

from opendrop.appfw import Presenter, TemplateChild, component, install


@component(
    template_path='./chooser.ui',
)
class ImageAcquisitionConfiguratorGenicamCameraChooserPresenter(Presenter):
    argument_entry: TemplateChild[Gtk.Entry] = TemplateChild('argument')
    ok_button: TemplateChild[Gtk.Button] = TemplateChild('ok_button')
    cancel_button: TemplateChild[Gtk.Button] = TemplateChild('cancel_button')
    error_label: TemplateChild[Gtk.Label] = TemplateChild('error_label')

    _initial_argument = ''
    
    def after_view_init(self) -> None:
        self.argument = self._initial_argument

    def argument_changed(self, *_) -> None:
        if self.argument == self._initial_argument:
            self.ok_button.props.label = 'Done'
        elif self.argument == '':
            self.ok_button.props.label = 'Clear'
        else:
            self.ok_button.props.label = 'Open'

    @install
    @GObject.Property(type=str, flags=GObject.ParamFlags.READWRITE|GObject.ParamFlags.CONSTRUCT_ONLY)
    def initial_argument(self) -> None:
        return self._initial_argument

    @initial_argument.setter
    def initial_argument(self, text: str) -> None:
        self._initial_argument = text

    @install
    @GObject.Property(type=str, flags=GObject.ParamFlags.READWRITE|GObject.ParamFlags.EXPLICIT_NOTIFY)
    def argument(self) -> None:
        return self.argument_entry.props.text

    @argument.setter
    def argument(self, text: str) -> None:
        self.argument_entry.props.text = text

    @install
    @GObject.Property(type=str)
    def error_text(self) -> None:
        return self.error_label.props.label

    @error_text.setter
    def error_text(self, text: str) -> None:
        self.error_label.props.label = text
