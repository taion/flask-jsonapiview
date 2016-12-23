from flask_resty import (
    Api, FixedSorting, GenericModelView, PrimaryKeySorting, Sorting,
)
from flask_resty.testing import assert_response
from marshmallow import fields, Schema
import pytest
from sqlalchemy import Column, Integer, String

# -----------------------------------------------------------------------------


@pytest.yield_fixture
def models(db):
    class Widget(db.Model):
        __tablename__ = 'widgets'

        id = Column(Integer, primary_key=True)
        name = Column(String)
        size = Column(Integer)

    db.create_all()

    yield {
        'widget': Widget,
    }

    db.drop_all()


@pytest.fixture
def schemas():
    class WidgetSchema(Schema):
        id = fields.Integer(as_string=True)
        name = fields.String()
        size = fields.Integer()

    return {
        'widget': WidgetSchema(),
    }


@pytest.fixture(autouse=True)
def routes(app, models, schemas):
    class WidgetListView(GenericModelView):
        model = models['widget']
        schema = schemas['widget']

        sorting = Sorting('name', 'size')

        def get(self):
            return self.list()

    class FixedWidgetListView(WidgetListView):
        sorting = FixedSorting('name,size')

        def get(self):
            return self.list()

    class PrimaryKeyWidgetListView(WidgetListView):
        sorting = PrimaryKeySorting()

        def get(self):
            return self.list()

    api = Api(app)
    api.add_resource('/widgets', WidgetListView)
    api.add_resource('/fixed_widgets', FixedWidgetListView)
    api.add_resource('/primary_key_widgets', PrimaryKeyWidgetListView)


@pytest.fixture(autouse=True)
def data(db, models):
    db.session.add_all((
        models['widget'](id=1, name="Foo", size=1),
        models['widget'](id=9, name="Foo", size=5),
        models['widget'](id=3, name="Baz", size=3),
    ))
    db.session.commit()


# -----------------------------------------------------------------------------


def test_single(client):
    response = client.get('/widgets?sort=size')

    assert_response(response, 200, [
        {
            'id': '1',
            'name': "Foo",
            'size': 1,
        },
        {
            'id': '3',
            'name': "Baz",
            'size': 3,
        },
        {
            'id': '9',
            'name': "Foo",
            'size': 5,
        },
    ])


def test_many(client):
    response = client.get('/widgets?sort=name,-size')

    assert_response(response, 200, [
        {
            'id': '3',
            'name': "Baz",
            'size': 3,
        },
        {
            'id': '9',
            'name': "Foo",
            'size': 5,
        },
        {
            'id': '1',
            'name': "Foo",
            'size': 1,
        },
    ])


def test_no_sort(client):
    response = client.get('/widgets')

    assert_response(response, 200, [
        {
            'id': '1',
            'name': "Foo",
            'size': 1,
        },
        {
            'id': '3',
            'name': "Baz",
            'size': 3,
        },
        {
            'id': '9',
            'name': "Foo",
            'size': 5,
        },
    ])


def test_fixed(client):
    response = client.get('/fixed_widgets')

    assert_response(response, 200, [
        {
            'id': '3',
            'name': "Baz",
            'size': 3,
        },
        {
            'id': '1',
            'name': "Foo",
            'size': 1,
        },
        {
            'id': '9',
            'name': "Foo",
            'size': 5,
        },
    ])


def test_primary_key_sort(client):
    response = client.get('/primary_key_widgets')

    assert_response(response, 200, [
        {
            'id': '1',
            'name': "Foo",
            'size': 1,
        },
        {
            'id': '3',
            'name': "Baz",
            'size': 3,
        },
        {
            'id': '9',
            'name': "Foo",
            'size': 5,
        },
    ])


# -----------------------------------------------------------------------------


def test_error_invalid_field(client):
    response = client.get('/widgets?sort=id')

    assert_response(response, 400, [{
        'code': 'invalid_sort',
        'source': {'parameter': 'sort'},
    }])


def test_error_empty(client):
    response = client.get('/widgets?sort=')
    assert_response(response, 400, [{
        'code': 'invalid_sort',
        'source': {'parameter': 'sort'},
    }])
