from mock import Mock

import pytest


@pytest.mark.gloop_application
async def test_quit(app):
    app.close()
