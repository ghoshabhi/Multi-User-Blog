import webtest
import main

def test_get():
    app = webtest.TestApp(main.app)

    response = app.get('/')

    assert response.status_int == 200
