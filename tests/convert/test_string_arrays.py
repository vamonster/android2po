"""Android supports string-arrays. Make sure we can handle them properly.
"""

from __future__ import absolute_import

from android2po import xml2po, po2xml
from StringIO import StringIO
from lxml import etree
from babel.messages.catalog import Catalog
from ..helpers import TestWarnFunc


def test_read_template():
    """Test basic read.
    """
    catalog = xml2po(StringIO('''
        <resources>
            <string-array name="colors">
                <item>red</item>
                <item>green</item>
            </string-array>
        </resources>
    '''))
    assert len(list(catalog)) == 3
    assert [m.context for m in catalog if m.id] == ['colors:0', 'colors:1']


def test_read_order():
    """Test that a strings of a string-array have the same position
    in the final catalog as the string-array had in the xml file, e.g.
    order is maintained for the string-array.
    """
    catalog = xml2po(StringIO('''
        <resources>
            <string name="before">foo</string>
            <string-array name="colors">
                <item>red</item>
                <item>green</item>
            </string-array>
            <string name="after">bar</string>
        </resources>
    '''))
    assert len(list(catalog)) == 5
    assert [m.context for m in catalog if m.id] == [
                'before', 'colors:0', 'colors:1', 'after']


def test_read_language():
    """Test that when reading a translated xml file, the translations
    of a string array are properly matched up with to strings in the
    untranslated template.
    """
    catalog, _ = xml2po(StringIO('''
        <resources>
            <string-array name="colors">
                <item>red</item>
                <item>green</item>
            </string-array>
        </resources>
    '''), StringIO('''
        <resources>
            <string-array name="colors">
                <item>rot</item>
                <item>gruen</item>
            </string-array>
        </resources>
    '''))

    assert len(list(catalog)) == 3
    assert [m.context for m in catalog if m.id] == ['colors:0', 'colors:1']
    assert [m.id for m in catalog if m.id] == ['red', 'green']
    assert [m.string for m in catalog if m.id] == ['rot', 'gruen']


def test_write():
    """Test writing a basic catalog.
    """
    catalog = Catalog()
    catalog.add('green', context='colors:0')
    catalog.add('red', context='colors:1')
    assert etree.tostring(po2xml(catalog)) == \
        '<resources><string-array name="colors"><item>green</item><item>red</item></string-array></resources>'


def test_write_order():
    """Test that when writing a catalog with string-arrays, order is
    maintained; both of the string-array tag in the list of all strings,
    as well as the array strings themselves.
    """
    catalog = Catalog()
    catalog.add('foo', 'foo', context='before')
    catalog.add('red', 'rot', context='colors:1')
    catalog.add('green', 'gruen', context='colors:0')
    catalog.add('bar', 'bar', context='after')
    print etree.tostring(po2xml(catalog))
    assert etree.tostring(po2xml(catalog)) == \
        '<resources><string name="before">foo</string><string-array name="colors"><item>gruen</item><item>rot</item></string-array><string name="after">bar</string></resources>'


def test_write_order_long_array():
    """[Regression] Test that order is maintained for a long array.
    """
    catalog = Catalog()
    catalog.add('foo', 'foo', context='before')
    expected_item_xml = ''
    for i in range(0, 13):
        catalog.add('loop%d' % i, 'schleife%d' % i, context='colors:%d' % i)
        expected_item_xml = expected_item_xml + '<item>%s</item>' % ('schleife%d' % i)
    catalog.add('bar', 'bar', context='after')
    assert etree.tostring(po2xml(catalog)) == \
        '<resources><string name="before">foo</string><string-array name="colors">%s</string-array><string name="after">bar</string></resources>' % expected_item_xml


def test_write_missing_translations():
    """[Regression] Specifically test that arrays are not written to the
    XML in an incomplete fashion if parts of the array are not translated.
    """
    catalog = Catalog()
    catalog.add('green', context='colors:0')    # does not have a translation
    catalog.add('red', 'rot', context='colors:1')
    assert etree.tostring(po2xml(catalog)) ==\
           '<resources><string-array name="colors"><item>green</item><item>rot</item></string-array></resources>'


def test_write_skipped_ids():
    """Test that arrays were ids are missing are written properly out as well.
    """
    # TODO: Indices missing at the end of the array will not be noticed,
    # because we are not aware of the arrays full length.
    # TODO: If we where smart enough to look in the original resource XML,
    # we could fill in missing array strings with the untranslated value.
    catalog = Catalog()
    catalog.add('red', context='colors:3')
    catalog.add('green', context='colors:1')
    assert etree.tostring(po2xml(catalog)) ==\
        '<resources><string-array name="colors"><item/><item>green</item><item/><item>red</item></string-array></resources>'


def test_unknown_escapes():
    """Test that unknown escapes are processed correctly, with a warning,
    for string-array items as well.
    """
    wfunc = TestWarnFunc()
    xml2po(StringIO('''
              <resources><string-array name="test">
                  <item>foo: \k</item>
              </string-array></resources>'''), warnfunc=wfunc)
    assert len(wfunc.logs) == 1
    assert 'unsupported escape' in wfunc.logs[0]
