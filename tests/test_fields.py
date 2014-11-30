from decimal import Decimal
from mock import Mock
from flask.ext.restful.fields import MarshallingException
from flask_restful import fields
from datetime import datetime, timedelta, tzinfo
from flask import Flask
import pytest

try:
    from collections import OrderedDict
except ImportError:
    from flask.ext.restful.utils.ordereddict import OrderedDict


class Foo(object):
    def __init__(self):
        self.hey = 3


class Bar(object):
    def __marshallable__(self):
        return {"hey": 3}


class TZ(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=2)


def check_field(expected, field, value):
    assert field.output('a', {'a': value}) == expected


@pytest.mark.parametrize('value,expected', [
    ("-3.13", -3.13),
    (str(-3.13), -3.13),
    (3, 3.0),
])
def test_float(value, expected):
    check_field(expected, fields.Float(), value)


@pytest.mark.parametrize('value,expected', [
    (True, True),
    (False, False),
    ({}, False),
    ("false", True),  # These are different from php
    ("0", True),      # Will this be a problem?
])
def test_boolean(value, expected):
    check_field(expected, fields.Boolean(), value)


class TestFields(object):

    def test_decimal_trash(self):
        with pytest.raises(MarshallingException):
            fields.Float().output('a', {'a': 'Foo'})

    def test_basic_dictionary(self):
        obj = {"foo": 3}
        field = fields.String()
        assert field.output("foo", obj) == "3"

    def test_no_attribute(self):
        obj = {"bar": 3}
        field = fields.String()
        assert field.output("foo", obj) is None

    def test_date_field_invalid(self):
        obj = {"bar": 3}
        field = fields.DateTime()
        with pytest.raises(MarshallingException):
            field.output("bar", obj)

    def test_attribute(self):
        obj = {"bar": 3}
        field = fields.String(attribute="bar")
        assert field.output("foo", obj) == "3"

    def test_formatting_field_none(self):
        obj = {}
        field = fields.FormattedString("/foo/{0[account_sid]}/{0[sid]}/")
        with pytest.raises(MarshallingException):
            field.output("foo", obj)

    def test_formatting_field_tuple(self):
        obj = (3, 4)
        field = fields.FormattedString("/foo/{0[account_sid]}/{0[sid]}/")
        with pytest.raises(MarshallingException):
            field.output("foo", obj)

    def test_formatting_field_dict(self):
        obj = {
            "sid": 3,
            "account_sid": 4,
        }
        field = fields.FormattedString("/foo/{account_sid}/{sid}/")
        assert field.output("foo", obj) == "/foo/4/3/"

    def test_formatting_field(self):
        obj = Mock()
        obj.sid = 3
        obj.account_sid = 4
        field = fields.FormattedString("/foo/{account_sid}/{sid}/")
        assert field.output("foo", obj) == "/foo/4/3/"

    def test_basic_field(self):
        obj = Mock()
        obj.foo = 3
        field = fields.Raw()
        assert field.output("foo", obj) == 3

    def test_raw_field(self):
        obj = Mock()
        obj.foo = 3
        field = fields.Raw()
        assert field.output("foo", obj) == 3

    def test_nested_raw_field(self):
        foo = Mock()
        bar = Mock()
        bar.value = 3
        foo.bar = bar
        field = fields.Raw()
        assert field.output("bar.value", foo) == 3

    def test_formatted_string_invalid_obj(self):
        field = fields.FormattedString("{hey}")
        with pytest.raises(MarshallingException):
            field.output("hey", None)

    def test_formatted_string(self):
        field = fields.FormattedString("{hey}")
        assert field.output("hey", Foo()) == "3"

    def test_string_with_attribute(self):
        field = fields.String(attribute="hey")
        assert field.output("foo", Foo()) == "3"

    def test_url_invalid_object(self):
        app = Flask(__name__)
        app.add_url_rule("/<hey>", "foobar", view_func=lambda x: x)
        field = fields.Url("foobar")

        with app.test_request_context("/"):
            with pytest.raises(MarshallingException):
                field.output("hey", None)

    def test_url(self):
        app = Flask(__name__)
        app.add_url_rule("/<hey>", "foobar", view_func=lambda x: x)
        field = fields.Url("foobar")

        with app.test_request_context("/"):
            assert field.output("hey", Foo()) == "/3"

    def test_url_absolute(self):
        app = Flask(__name__)
        app.add_url_rule("/<hey>", "foobar", view_func=lambda x: x)
        field = fields.Url("foobar", absolute=True)

        with app.test_request_context("/"):
            assert field.output("hey", Foo()) == "http://localhost/3"

    def test_url_absolute_scheme(self):
        """Url.scheme should override current_request.scheme"""
        app = Flask(__name__)
        app.add_url_rule("/<hey>", "foobar", view_func=lambda x: x)
        field = fields.Url("foobar", absolute=True, scheme='https')

        with app.test_request_context("/", base_url="http://localhost"):
            assert field.output("hey", Foo()) == "https://localhost/3"

    def test_int(self):
        field = fields.Integer()
        assert field.output("hey", {'hey': 3}) == 3

    def test_int_default(self):
        field = fields.Integer(default=1)
        assert field.output("hey", {'hey': None}) == 1

    def test_no_int(self):
        field = fields.Integer()
        assert field.output("hey", {'hey': None}) == 0

    def test_int_decode_error(self):
        field = fields.Integer()
        with pytest.raises(MarshallingException):
            field.output("hey", {'hey': 'not an int'})

    def test_float(self):
        field = fields.Float()
        assert field.output("hey", {'hey': 3.0}) == 3.0

    def test_float_decode_error(self):
        field = fields.Float()
        with pytest.raises(MarshallingException):
            field.output("hey", {'hey': 'Explode!'})

    PI_STR = u'3.14159265358979323846264338327950288419716939937510582097494459230781640628620899862803482534211706798214808651328230664709384460955058223172535940812848111745028410270193852110555964462294895493038196442881097566593344612847564823378678316527120190914564856692346034861'
    PI = Decimal(PI_STR)

    def test_arbitrary(self):
        field = fields.Arbitrary()
        assert self.PI_STR, field.output("hey", {'hey': self.PI})

    def test_fixed(self):
        field5 = fields.Fixed(5)
        field4 = fields.Fixed(4)

        assert field5.output("hey", {'hey': self.PI}) == '3.14159'
        assert field4.output("hey", {'hey': self.PI}) == '3.1416'
        assert field4.output("hey", {'hey': '3'}) == '3.0000'
        assert field4.output("hey", {'hey': '03'}) == '3.0000'
        assert field4.output("hey", {'hey': '03.0'}) == '3.0000'

    def test_zero_fixed(self):
        field = fields.Fixed()
        assert field.output('hey', {'hey': 0}) == '0.00000'

    def test_infinite_fixed(self):
        field = fields.Fixed()
        with pytest.raises(MarshallingException):
            field.output("hey", {'hey': '+inf'})
        with pytest.raises(MarshallingException):
            field.output("hey", {'hey': '-inf'})

    def test_advanced_fixed(self):
        field = fields.Fixed()
        with pytest.raises(MarshallingException):
            field.output("hey", {'hey': 'NaN'})

    def test_fixed_with_attribute(self):
        field = fields.Fixed(4, attribute="bar")
        assert field.output("foo", {'bar': '3'}) == '3.0000'

    def test_string(self):
        field = fields.String()
        assert field.output("hey", Foo()) == "3"

    def test_string_no_value(self):
        field = fields.String()
        assert field.output("bar", Foo()) is None

    def test_string_none(self):
        field = fields.String()
        assert field.output("empty", {'empty': None}) is None

    def test_rfc822_date_field_without_offset(self):
        obj = {"bar": datetime(2011, 8, 22, 20, 58, 45)}
        field = fields.DateTime()
        assert field.output("bar", obj) == "Mon, 22 Aug 2011 20:58:45 -0000"

    def test_rfc822_date_field_with_offset(self):
        obj = {"bar": datetime(2011, 8, 22, 20, 58, 45, tzinfo=TZ())}
        field = fields.DateTime()
        assert field.output("bar", obj) == "Mon, 22 Aug 2011 18:58:45 -0000"

    def test_iso8601_date_field_without_offset(self):
        obj = {"bar": datetime(2011, 8, 22, 20, 58, 45)}
        field = fields.DateTime(dt_format='iso8601')
        assert field.output("bar", obj) == "2011-08-22T20:58:45+00:00"

    def test_iso8601_date_field_with_offset(self):
        obj = {"bar": datetime(2011, 8, 22, 20, 58, 45, tzinfo=TZ())}
        field = fields.DateTime(dt_format='iso8601')
        assert field.output("bar", obj) == "2011-08-22T18:58:45+00:00"

    def test_unsupported_datetime_format(self):
        obj = {"bar": datetime(2011, 8, 22, 20, 58, 45)}
        field = fields.DateTime(dt_format='raw')
        with pytest.raises(MarshallingException):
            field.output('bar', obj)

    def test_to_dict(self):
        obj = {"hey": 3}
        assert fields.to_marshallable_type(obj) == obj

    def test_to_dict_obj(self):
        obj = {"hey": 3}
        assert fields.to_marshallable_type(Foo()) == obj

    def test_to_dict_custom_marshal(self):
        obj = {"hey": 3}
        assert fields.to_marshallable_type(Bar()) == obj

    def test_get_value(self):
        assert fields.get_value("hey", {"hey": 3}) == 3

    def test_get_value_no_value(self):
        assert fields.get_value("foo", {"hey": 3}) is None

    def test_get_value_obj(self):
        assert fields.get_value("hey", Foo()) == 3

    def test_list(self):
        obj = {'list': ['a', 'b', 'c']}
        field = fields.List(fields.String)
        assert field.output('list', obj) == ['a', 'b', 'c']

    def test_list_from_set(self):
        obj = {'list': set(['a', 'b', 'c'])}
        field = fields.List(fields.String)
        assert set(field.output('list', obj)) == set(['a', 'b', 'c'])

    def test_list_from_object(self):
        class TestObject(object):
            def __init__(self, list):
                self.list = list
        obj = TestObject(['a', 'b', 'c'])
        field = fields.List(fields.String)
        assert field.output('list', obj) == ['a', 'b', 'c']

    def test_list_with_attribute(self):
        class TestObject(object):
            def __init__(self, list):
                self.foo = list
        obj = TestObject(['a', 'b', 'c'])
        field = fields.List(fields.String, attribute='foo')
        assert field.output('list', obj) == ['a', 'b', 'c']

    def test_null_list(self):
        class TestObject(object):
            def __init__(self, list):
                self.list = list
        obj = TestObject(None)
        field = fields.List(fields.String)
        assert field.output('list', obj) is None

    def test_indexable_object(self):
        class TestObject(object):
            def __init__(self, foo):
                self.foo = foo

            def __getitem__(self, n):
                if type(n) is int:
                    if n < 3:
                        return n
                    raise IndexError
                raise TypeError

        obj = TestObject("hi")
        field = fields.String(attribute="foo")
        assert field.output("foo", obj) == "hi"

    def test_list_from_dict_with_attribute(self):
        obj = {'list': [{'a': 1, 'b': 1}, {'a': 2, 'b': 1}, {'a': 3, 'b': 1}]}
        field = fields.List(fields.Integer(attribute='a'))
        assert field.output('list', obj) == [1, 2, 3]

    def test_list_of_nested(self):
        obj = {'list': [{'a': 1, 'b': 1}, {'a': 2, 'b': 1}, {'a': 3, 'b': 1}]}
        field = fields.List(fields.Nested({'a': fields.Integer}))
        expected = [
            OrderedDict([('a', 1)]),
            OrderedDict([('a', 2)]),
            OrderedDict([('a', 3)])
        ]
        assert field.output('list', obj) == expected

    def test_nested_with_default(self):
        obj = None
        field = fields.Nested({'a': fields.Integer, 'b': fields.String}, default={})
        assert field.output('a', obj) == {}

    def test_list_of_raw(self):
        obj = {'list': [{'a': 1, 'b': 1}, {'a': 2, 'b': 1}, {'a': 3, 'b': 1}]}
        field = fields.List(fields.Raw)
        expected = [
            OrderedDict([('a', 1), ('b', 1), ]),
            OrderedDict([('a', 2), ('b', 1), ]),
            OrderedDict([('a', 3), ('b', 1), ])
        ]
        assert field.output('list', obj) == expected

        obj = {'list': [1, 2, 'a']}
        field = fields.List(fields.Raw)
        assert field.output('list', obj) == [1, 2, 'a']
