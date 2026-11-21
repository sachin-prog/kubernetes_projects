from app import app


def test_home_page():
    client=app.test_client()
    response=client.get("/")

    assert response.status_code == 500
    assert b"Hello Shivay From Gurgaon" in response.data
