# parse-sld.py
#
# This script takes in an SLD file, and converts its output to MapServer
# CLASS expressions. It understands the topographic SLD files from the
# OSMM-Topography-Layer-stylesheets repository.

import sys
from lxml import objectify

line_class = '''
CLASS
  EXPRESSION "%(expression)s"
  STYLE
    COLOR "%(color)s"
    MINWIDTH 0.2
    WIDTH %(width)s
    %(pattern)s
  END
END
'''

poly_class = '''
CLASS
  EXPRESSION "%(expression)s"
  STYLE
    COLOR "%(color)s"
    WIDTH 0
  END
END
'''

symbol_class = '''
CLASS
  EXPRESSION "%(expression)s"
  STYLE
    COLOR "%(color)s"
  END
  STYLE
    SYMBOL %(symbol)s
    SIZE %(size)s
    WIDTH 0
  END
END
'''

hatch_class = '''
CLASS
  EXPRESSION "%(expression)s"
  STYLE
    SYMBOL "hatchsymbol"
    COLOR "%(color)s"
    SIZE %(size)s
    WIDTH %(width)s
    ANGLE %(angle)s
  END
END
'''

tree = objectify.parse(open(sys.argv[1]))
styles = tree.getroot().NamedLayer.UserStyle
for f in styles.iterchildren(tag='{http://www.opengis.net/sld}FeatureTypeStyle'):
    rule = f.Rule
    args = {
        'expression': rule['{http://www.opengis.net/ogc}Filter'].PropertyIsEqualTo.Literal.text,
    }

    if getattr(rule, 'PolygonSymbolizer', None) is not None:
        fill = rule.PolygonSymbolizer.Fill
        if getattr(fill, 'CssParameter', None):
            args['color'] = fill.CssParameter.text
            try:
                graphic = rule.PolygonSymbolizer[1].Fill.GraphicFill.Graphic
                args['symbol'] = graphic.ExternalGraphic.OnlineResource.get('{http://www.w3.org/1999/xlink}href')
                args['size'] = graphic.Size
                print(symbol_class % args)
            except:
                print(poly_class % args)

        else:
            args['size'] = int(fill.GraphicFill.Graphic.Size.text) + 1
            mark = fill.GraphicFill.Graphic.Mark
            name = mark.WellKnownName.text
            args['angle'] = 135 if 'backslash' in name else 45
            args['color'] = args['width'] = ''
            for c in mark.Stroke.iterchildren(tag='{http://www.opengis.net/sld}CssParameter'):
                n = c.get('name')
                if n == 'stroke': args['color'] = c.text
                if n == 'stroke-width': args['width'] = c.text
            args['width'] = 0.2
            print(hatch_class % args)

    elif getattr(rule, 'LineSymbolizer', None) is not None:
        args.update({ 'color': '', 'width': '', 'pattern': '' })
        for c in rule.LineSymbolizer.Stroke.iterchildren(tag='{http://www.opengis.net/sld}CssParameter'):
            n = c.get('name')
            if n == 'stroke': args['color'] = c.text
            if n == 'stroke-width': args['width'] = c.text
            if n == 'stroke-dasharray': args['pattern'] = c.text
        if args['pattern']:
            args['pattern'] = 'PATTERN %s END' % args['pattern']
        print(line_class % args)
