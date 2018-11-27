import pytest
from bikewheelapi import app

@pytest.fixture
def client(request):
	test_client = app.test_client()

	return test_client


def test_hello_world(client):
	response = client.get('/')
	assert b'Hello World' in response.data
