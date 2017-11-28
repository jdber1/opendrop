class ViewPresenterMap:
    def __init__(self, views, presenters):
        self.view_to_presenters = {
            view: self._find_presenter_for_view(view, presenters)
            for view in views
        }

    @staticmethod
    def _find_presenter_for_view(view, presenters):
        for presenter in presenters:
            if presenter.can_present(view):
                return presenter

    def presenter_from_view(self, view):
        return self.view_to_presenters[view]

    def view_from_presenter(self, needle_presenter):
        for view, presenter in self.view_to_presenters.items():
            if presenter == needle_presenter:
                return view

