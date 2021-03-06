###############################################################################
#
# Copyright (c) 2011 Ruslan Spivak
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

__author__ = 'Ruslan Spivak <ruslan.spivak@gmail.com>'


class Node(object):
    def __init__(self, children=None, lineno=-1):
        self._children_list = [] if children is None else children
        self.lineno = lineno
        self.parent = None

    def __iter__(self):
        for child in self.children():
            if child is not None:
                yield child

    def children(self):
        return self._children_list

    def to_ecma(self, *args, **kwargs):
        # Can't import at module level as ecmavisitor depends
        # on ast module...
        from slimit.visitors.ecmavisitor import ECMAVisitor
        visitor = ECMAVisitor(*args, **kwargs)
        return visitor.visit(self)

    def replace_self(self, replacement):
        """
            Replace this node in the AST with a new node

            This is necessary if we want to change the type of a node in the AST
            (e.g. replace a function call with a string literal) since we can't
            rebind the whole object, just mutate the properties of the existing
            object.

            Massive hack, but it works.
        """
        assert self.parent is not None, "Can't do replacement without parent"

        # get all valid attribs
        attribs = [a for a in dir(self.parent)
                    if a[0] != '_' and
                       a not in ['children', 'to_ecma']]

        # replace all instances of self in the parent
        for attrib in attribs:
            attr_val = getattr(self.parent, attrib, None)
            if not attr_val:
                continue

            # if it's a list, check all members of the list for this node
            if isinstance(attr_val, list):
                for i in xrange(len(attr_val)):
                    if attr_val[i] == self:
                        attr_val[i] = replacement
            # if it's a value, check to see if it's equal & make replacement
            elif attr_val == self:
                setattr(self.parent, attrib, replacement)


class Program(Node):
    pass

class Block(Node):
    pass

class ValNode(Node):
    def __init__(self, value, *args, **kwargs):
        self.value = value
        super(ValNode, self).__init__(*args, **kwargs)

    def childer(self):
        return []

class Boolean(ValNode):
    pass

class Null(ValNode):
    pass

class Number(ValNode):
    pass

class Identifier(ValNode):
    pass

class String(ValNode):
    pass

class Regex(ValNode):
    pass

class Array(Node):
    def __init__(self, items, *args, **kwargs):
        self.items = items
        super(Array, self).__init__(*args, **kwargs)

    def children(self):
        return self.items

class Object(Node):
    def __init__(self, properties=None, *args, **kwargs):
        self.properties = [] if properties is None else properties
        super(Object, self).__init__(*args, **kwargs)

    def children(self):
        return self.properties

class NewExpr(Node):
    def __init__(self, identifier, args=None, *_args, **kwargs):
        self.identifier = identifier
        self.args = [] if args is None else args
        super(NewExpr, self).__init__(*_args, **kwargs)

    def children(self):
        return [self.identifier, self.args]

class FunctionCall(Node):
    def __init__(self, identifier, args=None, *_args, **kwargs):
        self.identifier = identifier
        self.args = [] if args is None else args
        super(FunctionCall, self).__init__(*_args, **kwargs)

    def children(self):
        return [self.identifier] + self.args

class BracketAccessor(Node):
    def __init__(self, node, expr, *args, **kwargs):
        self.node = node
        self.expr = expr
        super(BracketAccessor, self).__init__(*args, **kwargs)

    def children(self):
        return [self.node, self.expr]

class DotAccessor(Node):
    def __init__(self, node, identifier, *args, **kwargs):
        self.node = node
        self.identifier = identifier
        super(DotAccessor, self).__init__(*args, **kwargs)

    def children(self):
        return [self.node, self.identifier]

class Assign(Node):
    def __init__(self, op, left, right, *args, **kwargs):
        self.op = op
        self.left = left
        self.right = right
        super(Assign, self).__init__(*args, **kwargs)

    def children(self):
        return [self.left, self.right]

class GetPropAssign(Node):
    def __init__(self, prop_name, elements, *args, **kwargs):
        """elements - function body"""
        self.prop_name = prop_name
        self.elements = elements
        super(GetPropAssign, self).__init__(*args, **kwargs)

    def children(self):
        return [self.prop_name] + self.elements

class SetPropAssign(Node):
    def __init__(self, prop_name, parameters, elements, *args, **kwargs):
        """elements - function body"""
        self.prop_name = prop_name
        self.parameters = parameters
        self.elements = elements
        super(SetPropAssign, self).__init__(*args, **kwargs)

    def children(self):
        return [self.prop_name] + self.parameters + self.elements

class VarStatement(Node):
    pass

class VarDecl(Node):
    def __init__(self, identifier, initializer=None, *args, **kwargs):
        self.identifier = identifier
        self.identifier._mangle_candidate = True
        self.initializer = initializer
        super(VarDecl, self).__init__(*args, **kwargs)

    def children(self):
        return [self.identifier, self.initializer]

class UnaryOp(Node):
    def __init__(self, op, value, postfix=False, *args, **kwargs):
        self.op = op
        self.value = value
        self.postfix = postfix
        super(UnaryOp, self).__init__(*args, **kwargs)

    def children(self):
        return [self.value]

class BinOp(Node):
    def __init__(self, op, left, right, *args, **kwargs):
        self.op = op
        self.left = left
        self.right = right
        super(BinOp, self).__init__(*args, **kwargs)

    def children(self):
        return [self.left, self.right]

class Conditional(Node):
    """Conditional Operator ( ? : )"""
    def __init__(self, predicate, consequent, alternative, *args, **kwargs):
        self.predicate = predicate
        self.consequent = consequent
        self.alternative = alternative
        super(Conditional, self).__init__(*args, **kwargs)

    def children(self):
        return [self.predicate, self.consequent, self.alternative]

class If(Node):
    def __init__(self, predicate, consequent, alternative=None, *args,
            **kwargs):
        self.predicate = predicate
        self.consequent = consequent
        self.alternative = alternative
        super(If, self).__init__(*args, **kwargs)

    def children(self):
        return [self.predicate, self.consequent, self.alternative]

class DoWhile(Node):
    def __init__(self, predicate, statement, *args, **kwargs):
        self.predicate = predicate
        self.statement = statement
        super(DoWhile, self).__init__(*args, **kwargs)

    def children(self):
        return [self.predicate, self.statement]

class While(Node):
    def __init__(self, predicate, statement, *args, **kwargs):
        self.predicate = predicate
        self.statement = statement
        super(While, self).__init__(*args, **kwargs)

    def children(self):
        return [self.predicate, self.statement]

class For(Node):
    def __init__(self, init, cond, count, statement, *args, **kwargs):
        self.init = init
        self.cond = cond
        self.count = count
        self.statement = statement
        super(For, self).__init__(*args, **kwargs)

    def children(self):
        return [self.init, self.cond, self.count, self.statement]

class ForIn(Node):
    def __init__(self, item, iterable, statement, *args, **kwargs):
        self.item = item
        self.iterable = iterable
        self.statement = statement
        super(ForIn, self).__init__(*args, **kwargs)

    def children(self):
        return [self.item, self.iterable, self.statement]

class Continue(Node):
    def __init__(self, identifier=None, *args, **kwargs):
        self.identifier = identifier
        super(Continue, self).__init__(*args, **kwargs)

    def children(self):
        return [self.identifier]

class Break(Node):
    def __init__(self, identifier=None, *args, **kwargs):
        self.identifier = identifier
        super(Break, self).__init__(*args, **kwargs)

    def children(self):
        return [self.identifier]

class Return(Node):
    def __init__(self, expr=None, *args, **kwargs):
        self.expr = expr
        super(Return, self).__init__(*args, **kwargs)

    def children(self):
        return [self.expr]

class With(Node):
    def __init__(self, expr, statement, *args, **kwargs):
        self.expr = expr
        self.statement = statement
        super(With, self).__init__(*args, **kwargs)

    def children(self):
        return [self.expr, self.statement]

class Switch(Node):
    def __init__(self, expr, cases, default=None, *args, **kwargs):
        self.expr = expr
        self.cases = cases
        self.default = default
        super(Switch, self).__init__(*args, **kwargs)

    def children(self):
        return [self.expr] + self.cases + [self.default]

class Case(Node):
    def __init__(self, expr, elements, *args, **kwargs):
        self.expr = expr
        self.elements = elements if elements is not None else []
        super(Case, self).__init__(*args, **kwargs)

    def children(self):
        return [self.expr] + self.elements

class Default(Node):
    def __init__(self, elements, *args, **kwargs):
        self.elements = elements if elements is not None else []
        super(Default, self).__init__(*args, **kwargs)

    def children(self):
        return self.elements

class Label(Node):
    def __init__(self, identifier, statement, *args, **kwargs):
        self.identifier = identifier
        self.statement = statement
        super(Label, self).__init__(*args, **kwargs)

    def children(self):
        return [self.identifier, self.statement]

class Throw(Node):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(Throw, self).__init__(*args, **kwargs)

    def children(self):
        return [self.expr]

class Try(Node):
    def __init__(self, statements, catch=None, fin=None, *args, **kwargs):
        self.statements = statements
        self.catch = catch
        self.fin = fin
        super(Try, self).__init__(*args, **kwargs)

    def children(self):
        return [self.statements] + [self.catch, self.fin]

class Catch(Node):
    def __init__(self, identifier, elements, *args, **kwargs):
        self.identifier = identifier
        # CATCH identifiers are subject to name mangling. we need to mark them.
        self.identifier._mangle_candidate = True
        self.elements = elements
        super(Catch, self).__init__(*args, **kwargs)

    def children(self):
        return [self.identifier, self.elements]

class Finally(Node):
    def __init__(self, elements, *args, **kwargs):
        self.elements = elements
        super(Finally, self).__init__(*args, **kwargs)

    def children(self):
        return self.elements

class Debugger(Node):
    def __init__(self, value, *args, **kwargs):
        self.value = value
        super(Debugger, self).__init__(*args, **kwargs)

    def children(self):
        return []


class FuncBase(Node):
    def __init__(self, identifier, parameters, elements, *args, **kwargs):
        self.identifier = identifier
        self.parameters = parameters if parameters is not None else []
        self.elements = elements if elements is not None else []
        self._init_ids()
        super(FuncBase, self).__init__(*args, **kwargs)

    def _init_ids(self):
        # function declaration/expression name and parameters are identifiers
        # and therefore are subject to name mangling. we need to mark them.
        if self.identifier is not None:
            self.identifier._mangle_candidate = True
        for param in self.parameters:
            param._mangle_candidate = True

    def children(self):
        return [self.identifier] + self.parameters + self.elements

class FuncDecl(FuncBase):
    pass

# The only difference is that function expression might not have an identifier
class FuncExpr(FuncBase):
    pass


class Comma(Node):
    def __init__(self, left, right, *args, **kwargs):
        self.left = left
        self.right = right
        super(Comma, self).__init__(*args, **kwargs)

    def children(self):
        return [self.left, self.right]

class EmptyStatement(Node):
    def __init__(self, value, *args, **kwargs):
        self.value = value
        super(EmptyStatement, self).__init__(*args, **kwargs)

    def children(self):
        return []

class ExprStatement(Node):
    def __init__(self, expr, *args, **kwargs):
        self.expr = expr
        super(ExprStatement, self).__init__(*args, **kwargs)

    def children(self):
        return [self.expr]

class Elision(Node):
    def __init__(self, value, *args, **kwargs):
        self.value = value
        super(Elision, self).__init__(*args, **kwargs)

    def children(self):
        return []

class This(Node):
    def __init__(self, *args, **kwargs):
        super(This, self).__init__(*args, **kwargs)

    def children(self):
        return []
