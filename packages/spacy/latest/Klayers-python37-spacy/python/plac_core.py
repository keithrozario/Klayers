# this module should be kept Python 2.3 compatible
import re
import sys
import inspect
import argparse
from gettext import gettext as _
if sys.version >= '3':
    from inspect import getfullargspec
else:
    class getfullargspec(object):
        "A quick and dirty replacement for getfullargspec for Python 2.X"
        def __init__(self, f):
            self.args, self.varargs, self.varkw, self.defaults = \
                inspect.getargspec(f)
            self.annotations = getattr(f, '__annotations__', {})


def getargspec(callableobj):
    """Given a callable return an object with attributes .args, .varargs,
    .varkw, .defaults. It tries to do the "right thing" with functions,
    methods, classes and generic callables."""
    if inspect.isfunction(callableobj):
        argspec = getfullargspec(callableobj)
    elif inspect.ismethod(callableobj):
        argspec = getfullargspec(callableobj)
        del argspec.args[0]  # remove first argument
    elif inspect.isclass(callableobj):
        if callableobj.__init__ is object.__init__:  # to avoid an error
            argspec = getfullargspec(lambda self: None)
        else:
            argspec = getfullargspec(callableobj.__init__)
        del argspec.args[0]  # remove first argument
    elif hasattr(callableobj, '__call__'):
        argspec = getfullargspec(callableobj.__call__)
        del argspec.args[0]  # remove first argument
    else:
        raise TypeError(_('Could not determine the signature of ') +
                        str(callableobj))
    return argspec


def annotations(**ann):
    """
    Returns a decorator annotating a function with the given annotations.
    This is a trick to support function annotations in Python 2.X.
    """
    def annotate(f):
        fas = getfullargspec(f)
        args = fas.args
        if fas.varargs:
            args.append(fas.varargs)
        if fas.varkw:
            args.append(fas.varkw)
        for argname in ann:
            if argname not in args:
                raise NameError(
                    _('Annotating non-existing argument: %s') % argname)
        f.__annotations__ = ann
        return f
    return annotate


def is_annotation(obj):
    """
    An object is an annotation object if it has the attributes
    help, kind, abbrev, type, choices, metavar.
    """
    return (hasattr(obj, 'help') and hasattr(obj, 'kind')
            and hasattr(obj, 'abbrev') and hasattr(obj, 'type')
            and hasattr(obj, 'choices') and hasattr(obj, 'metavar'))


class Annotation(object):
    def __init__(self, help=None, kind="positional", abbrev=None, type=None,
                 choices=None, metavar=None):
        assert kind in ('positional', 'option', 'flag'), kind
        if kind == "positional":
            assert abbrev is None, abbrev
        self.help = help
        self.kind = kind
        self.abbrev = abbrev
        self.type = type
        self.choices = choices
        self.metavar = metavar

    def from_(cls, obj):
        "Helper to convert an object into an annotation, if needed"
        if is_annotation(obj):
            return obj  # do nothing
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
            return cls(*obj)
        return cls(obj)
    from_ = classmethod(from_)


NONE = object()  # sentinel use to signal the absence of a default

PARSER_CFG = getfullargspec(argparse.ArgumentParser.__init__).args[1:]
# the default arguments accepted by an ArgumentParser object


def pconf(obj):
    "Extracts the configuration of the underlying ArgumentParser from obj"
    cfg = dict(description=obj.__doc__,
               formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in dir(obj):
        if name in PARSER_CFG:  # argument of ArgumentParser
            cfg[name] = getattr(obj, name)
    return cfg

_parser_registry = {}


def parser_from(obj, **confparams):
    """
    obj can be a callable or an object with a .commands attribute.
    Returns an ArgumentParser.
    """
    try:  # the underlying parser has been generated already
        return _parser_registry[obj]
    except KeyError:  # generate a new parser
        pass
    conf = pconf(obj).copy()
    conf.update(confparams)
    _parser_registry[obj] = parser = ArgumentParser(**conf)
    parser.obj = obj
    parser.case_sensitive = confparams.get(
        'case_sensitive', getattr(obj, 'case_sensitive', True))
    if hasattr(obj, 'commands') and not inspect.isclass(obj):
        # a command container instance
        parser.addsubcommands(obj.commands, obj, 'subcommands')
    else:
        parser.populate_from(obj)
    return parser


def _extract_kwargs(args):
    "Returns two lists: regular args and name=value args"
    arglist = []
    kwargs = {}
    for arg in args:
        match = re.match(r'([a-zA-Z_]\w*)=', arg)
        if match:
            name = match.group(1)
            kwargs[name] = arg[len(name)+1:]
        else:
            arglist.append(arg)
    return arglist, kwargs


def _match_cmd(abbrev, commands, case_sensitive=True):
    "Extract the command name from an abbreviation or raise a NameError"
    if not case_sensitive:
        abbrev = abbrev.upper()
        commands = [c.upper() for c in commands]
    perfect_matches = [name for name in commands if name == abbrev]
    if len(perfect_matches) == 1:
        return perfect_matches[0]
    matches = [name for name in commands if name.startswith(abbrev)]
    n = len(matches)
    if n == 1:
        return matches[0]
    elif n > 1:
        raise NameError(
            _('Ambiguous command %r: matching %s' % (abbrev, matches)))


class ArgumentParser(argparse.ArgumentParser):
    """
    An ArgumentParser with .func and .argspec attributes, and possibly
    .commands and .subparsers.
    """
    case_sensitive = True

    def alias(self, arg):
        "Can be overridden to preprocess command-line arguments"
        return arg

    def consume(self, args):
        """Call the underlying function with the args. Works also for
        command containers, by dispatching to the right subparser."""
        arglist = [self.alias(a) for a in args]
        cmd = None
        if hasattr(self, 'subparsers'):
            subp, cmd = self._extract_subparser_cmd(arglist)
            if subp is None and cmd is not None:
                return cmd, self.missing(cmd)
            elif subp is not None:  # use the subparser
                self = subp
        if hasattr(self, 'argspec') and self.argspec.varkw:
            arglist, kwargs = _extract_kwargs(arglist)  # modify arglist!
        else:
            kwargs = {}
        if hasattr(self, 'argspec') and self.argspec.varargs:
            # ignore unrecognized arguments
            ns, extraopts = self.parse_known_args(arglist)
        else:
            ns, extraopts = self.parse_args(arglist), []  # may raise an exit
        if not hasattr(self, 'argspec'):
            raise SystemExit
        args = [getattr(ns, a) for a in self.argspec.args]
        varargs = getattr(ns, self.argspec.varargs or '', [])
        collision = set(self.argspec.args) & set(kwargs)
        if collision:
            self.error(
                _('colliding keyword arguments: %s') % ' '.join(collision))
        return cmd, self.func(*(args + varargs + extraopts), **kwargs)

    def _extract_subparser_cmd(self, arglist):
        "Extract the right subparser from the first recognized argument"
        optprefix = self.prefix_chars[0]
        name_parser_map = self.subparsers._name_parser_map
        for i, arg in enumerate(arglist):
            if not arg.startswith(optprefix):
                cmd = _match_cmd(arg, name_parser_map, self.case_sensitive)
                del arglist[i]
                return name_parser_map.get(cmd), cmd or arg
        return None, None

    def addsubcommands(self, commands, obj, title=None, cmdprefix=''):
        "Extract a list of subcommands from obj and add them to the parser"
        if hasattr(obj, cmdprefix) and obj.cmdprefix in self.prefix_chars:
            raise ValueError(_('The prefix %r is already taken!' % cmdprefix))
        if not hasattr(self, 'subparsers'):
            self.subparsers = self.add_subparsers(title=title)
        elif title:
            self.add_argument_group(title=title)  # populate ._action_groups
        prefixlen = len(getattr(obj, 'cmdprefix', ''))
        add_help = getattr(obj, 'add_help', True)
        for cmd in commands:
            func = getattr(obj, cmd[prefixlen:])  # strip the prefix
            self.subparsers.add_parser(
                cmd, add_help=add_help, help=func.__doc__, **pconf(func)
                ).populate_from(func)

    def _set_func_argspec(self, obj):
        """Extracts the signature from a callable object and adds an .argspec
        attribute to the parser. Also adds a .func reference to the object."""
        self.func = obj
        self.argspec = getargspec(obj)
        _parser_registry[obj] = self

    def populate_from(self, func):
        """
        Extract the arguments from the attributes of the passed function
        and return a populated ArgumentParser instance.
        """
        self._set_func_argspec(func)
        f = self.argspec
        defaults = f.defaults or ()
        n_args = len(f.args)
        n_defaults = len(defaults)
        alldefaults = (NONE,) * (n_args - n_defaults) + defaults
        prefix = self.prefix = getattr(func, 'prefix_chars', '-')[0]
        for name, default in zip(f.args, alldefaults):
            ann = f.annotations.get(name, ())
            a = Annotation.from_(ann)
            metavar = a.metavar
            if default is NONE:
                dflt = None
            else:
                dflt = default
                if a.help is None:
                    a.help = '[%s]' % str(dflt)  # dflt can be a tuple
            if a.kind in ('option', 'flag'):
                if a.abbrev:
                    shortlong = (prefix + a.abbrev,
                                 prefix*2 + name.replace('_', '-'))
                else:
                    shortlong = (prefix + name.replace('_', '-'),)
            elif default is NONE:  # required argument
                self.add_argument(name, help=a.help, type=a.type,
                                  choices=a.choices, metavar=metavar)
            else:  # default argument
                self.add_argument(
                    name, nargs='?', help=a.help, default=dflt,
                    type=a.type, choices=a.choices, metavar=metavar)
            if a.kind == 'option':
                if default is not NONE:
                    metavar = metavar or str(default)
                self.add_argument(
                    help=a.help, default=dflt, type=a.type,
                    choices=a.choices, metavar=metavar, *shortlong)
            elif a.kind == 'flag':
                if default is not NONE and default is not False:
                    raise TypeError(_('Flag %r wants default False, got %r') %
                                    (name, default))
                self.add_argument(action='store_true', help=a.help, *shortlong)
        if f.varargs:
            a = Annotation.from_(f.annotations.get(f.varargs, ()))
            self.add_argument(f.varargs, nargs='*', help=a.help, default=[],
                              type=a.type, metavar=a.metavar)
        if f.varkw:
            a = Annotation.from_(f.annotations.get(f.varkw, ()))
            self.add_argument(f.varkw, nargs='*', help=a.help, default={},
                              type=a.type, metavar=a.metavar)

    def missing(self, name):
        "May raise a SystemExit"
        miss = getattr(self.obj, '__missing__', lambda name:
                       self.error('No command %r' % name))
        return miss(name)

    def print_actions(self):
        "Useful for debugging"
        print(self)
        for a in self._actions:
            print(a)


def iterable(obj):
    "Any object with an __iter__ method which is not a string"
    return hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes))


def call(obj, arglist=sys.argv[1:], eager=True, version=None):
    """
    If obj is a function or a bound method, parse the given arglist
    by using the parser inferred from the annotations of obj
    and call obj with the parsed arguments.
    If obj is an object with attribute .commands, dispatch to the
    associated subparser.
    """
    parser = parser_from(obj)
    if version:
        parser.add_argument(
            '--version', '-v', action='version', version=version)
    cmd, result = parser.consume(arglist)
    if iterable(result) and eager:  # listify the result
        return list(result)
    return result
