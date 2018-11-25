"""
A lazy iterator type inspired by Rust's iterator types.

You can extend your own types to use this iterator interface by inheriting
and overriding the __next__ method.

You can also use the ``into_iter`` function, which accepts any Python iterable
and returns an Iterator.

Basic usage
-----------

If you already have something that's iterable, use the ``into_iter`` function::

    iter = into_iter([1, 2, 3])

It accepts any kind of iterable, so all of the following will work::

    iter = into_iter([x for x in xs]) # list comprehension
    iter = into_iter(x for x in xs)   # generator expression
    iter = into_iter(range(10))       # generator
    iter = into_iter(my_list)         # list

In order to collect the results back into a list, use :meth:`~iterator.Iterator.collect`::

    assert into_iter([1, 2, 3]).collect() == [1, 2, 3]

Iterator methods
~~~~~~~~~~~~~~~~

Perhaps the most used methods are :meth:`~iterator.Iterator.map` and
:meth:`~iterator.Iterator.filter`. See below::

    result = into_iter(range(5))\\
    .map(lambda x: 2*x)\\
    .filter(lambda x: x < 7)\\
    .collect()

    assert result == [2, 4, 6]

:meth:`~iterator.Iterator.map` yields the result of applying the function to each
element, and :meth:`~iterator.Iterator.filter` only yields items for which the
function returns ``True``.

There's also :meth:`~iterator.Iterator.collect` which collects the elements of the
iterator into (by default) a list, but can also be provided with a function to
collect into.

For example, collecting into a dict::

    result = into_iter("abc")\\
        .zip(range(3))\\
        .collect(dict)

    assert result == {'a':0, 'b':1, 'c':2}

Or::

    with open("my_data.json") as f:
        df = into_iter(json.load(f))\\
            .map(some_operation)\\
            .filter(stuff_wanted)\\
            .collect(pandas.DataFrame)

"""


def into_iter(iterable):
    """Creates an Iterator from the iterable."""

    class IntoIterator(Iterator):
        def __init__(self, iterable):
            self.wrapped = iterable

        def __next__(self):
            return next(self.wrapped)

    return IntoIterator(iter(iterable))


class Iterator:
    """
    A lazy iterator type inspired by Rust iterators.

    See the module-level documentation for more information.
    """

    def __init__(self):
        pass

    def __iter__(self):
        return self

    def __next__(self):
        """
        Return the next value in the iterator.

        .. note::
            You should override this method for your type.
        """
        raise StopIteration

    def count(self):
        """
        Consume the iterator, counting the number of iterations and returning it.

        :return: the number of items in the iterator.

        .. note::
            This function will not return if your iterator is infinite (e.g created
            by :meth:`~iterator.Iterator.cycle` or a generator which never exits).
        """
        counter = 0
        for i in self:
            counter += 1

        return counter

    def last(self):
        """
        :return: the last item in the iterator.
        :raises LookupError: if the iterator is empty.
        """
        item = []
        for i in self:
            if not item:
                item.append(i)
            else:
                item[0] = i

        if not item:
            raise LookupError

        return item[0]

    def filter(self, pred):
        """
        Applies the predicate ``pred`` to each element in the iterator.

        :param fn(A)->bool pred: a function which returns ``True`` if the item
        should be kept.
        :return: a stream of values for which the predicate is true.
        """

        class Filter(Iterator):
            def __init__(self, wrapped, pred):
                self.wrapped = wrapped
                self.pred = pred

            def __next__(self):
                result = next(self.wrapped)
                if self.pred(result):
                    return result
                else:
                    return next(self)

        return Filter(self, pred)

    def flatten(self):
        """
        Transform an iterator of iterables into one long iterator.

        Example::

            assert into_iter([[1, 2], [3, 4]]).flatten().collect() == [1, 2, 3, 4]
        """

        class Flatten(Iterator):
            def __init__(self, wrapped):
                self.wrapped = wrapped
                self.current = iter(next(self.wrapped))

            def __next__(self):
                try:
                    return next(self.current)
                except StopIteration:
                    self.current = iter(next(self.wrapped))
                    return next(self)

        return Flatten(self)

    def map(self, op):
        """
        Applies the transformation ``op`` to each element of the iterator.

        :param fn(A)->B op: the transformation to apply to each element of the iterator.

        Example::

            result = into_iter([1, 2, 3])\\
                .map(lambda x: 2*x)\\
                .collect()
                
            assert result == [2, 4, 6]

        """

        class Map(Iterator):
            def __init__(self, wrapped, op):
                self.wrapped = wrapped
                self.op = op

            def __next__(self):
                return self.op(next(self.wrapped))

        return Map(self, op)

    def flat_map(self, op):
        """
        Applies :meth:`map` followed by :meth:`flatten`.
        """

        return self.map(op).flatten()

    def filter_map(self, op):
        """
        :param func op: each element in the iterator will be passed to this function.
        If the function raises :exception:`ValueError`, then the element will be
        filtered out. Otherwise, yield the result of the function.

        Example::

            def my_op(x):
                if x < 3:
                    return 2*x
                else:
                    raise ValueError

            result = into_iter(range(5))\\
            .filter_map(my_op)\\
            .collect()

            assert result == [0, 2, 4]
        """

        class FilterMap(Iterator):
            def __init__(self, wrapped, op):
                self.wrapped = wrapped
                self.op = op

            def __next__(self):
                try:
                    return self.op(next(self.wrapped))
                except ValueError:
                    return next(self)

        return FilterMap(self, op)

    def zip(self, *args):
        """
        Transforms a group of streams into a stream of groups, via the Python
        builtin.

        Example::

            result = into_iter(range(5)).zip(range(5,10)).collect()
            assert result == [(0,5), (1,6), (2,7), (3,8), (4,9)]

        .. note::
            Unlike the Rust equivalent, this function can accept a variable
            number of arguments.
        """

        class Zip(Iterator):
            def __init__(self, wrapped, *args):
                self.wrapped = zip(wrapped, *args)

            def __next__(self):
                return next(self.wrapped)

        return Zip(self, *args)

    def chain(self, other):
        """
        When the elements in the iterator are exhausted, starts yielding elements
        from ``other``, chaining them together.
        """

        class Chain(Iterator):
            def __init__(self, wrapped, other):
                self.wrapped = wrapped
                self.other = other
                self.first_done = False

            def __next__(self):
                if not self.first_done:
                    try:
                        return next(self.wrapped)
                    except StopIteration:
                        self.first_done = True

                return next(self.other)

        return Chain(self, other)

    def enumerate(self):
        """Enumerate the stream, via the Python builtin."""

        class Enumerate(Iterator):
            def __init__(self, wrapped):
                self.enum = enumerate(wrapped)

            def __next__(self):
                return next(self.enum)

        return Enumerate(self)

    def peekable(self):
        """
        Return an iterator with an additional method, `peek`, which can get the
        the next element in the stream without advancing the iterator.
        """

        class Peekable(Iterator):
            def __init__(self, wrapped):
                self.wrapped = wrapped
                self.peeked = []

            def __next__(self):
                if self.peeked:
                    item = self.peeked[0]
                    self.peeked = []
                    return item
                else:
                    return self.peek()

            def peek(self):
                if not self.peeked:
                    self.peeked = [next(self.wrapped)]

                return self.peeked[0]

        return Peekable(self)

    def skip_while(self, op):
        """Skip elements while predicate is true."""

        class SkipWhile(Iterator):
            def __init__(self, wrapped, op):
                self.wrapped = wrapped
                self.op = op
                self.done = False

            def __next__(self):
                if self.done:
                    return next(self.wrapped)
                else:
                    item = next(self.wrapped)
                    while self.op(item):
                        item = next(self.wrapped)

                    self.done = True
                    return item

        return SkipWhile(self, op)

    def take_while(self, op):
        """Take elements until predicate is false."""

        class TakeWhile(Iterator):
            def __init__(self, wrapped, op):
                self.wrapped = wrapped
                self.op = op
                self.done = False

            def __next__(self):
                if self.done:
                    raise StopIteration
                else:
                    item = next(self.wrapped)
                    if self.op(item):
                        return item
                    else:
                        self.done = True
                        next(self)

        return TakeWhile(self, op)

    def inspect(self, op):
        """
        Do something with each element of an iterator. Different to `map`; `map`
        essentially does::

            [ f(x) for x in xs ]

        Compare to this method, which essentially does::

            [ (f(x), x)[1] for x in xs ]

        In other words, :meth:`map` applies a function to each element of the iterator
        and returns the *result*, :meth:`inspect` applies a function to each element of
        the iterator and returns *the element*.

        This can be useful e.g for logging errors before filtering them out::

            def log_if_bad(egg):
                if egg.is_bad():
                    print("bad egg will be removed")
                else:
                    pass

            my_iter\\
            .map(lambda x: some_operation(x))\\
            .inspect(lambda e: log_if_bad(e))\\
            .filter(lambda e: not e.is_bad())

        """

        class Inspect(Iterator):
            def __init__(self, wrapped, op):
                self.wrapped = wrapped
                self.op = op

            def __next__(self):
                item = next(self.wrapped)
                self.op(item)
                return item

        return Inspect(self, op)

    def partition(self, op):
        """
        Consume the Iterator, splitting the elements into two lists based
        on whether or not they satisfy the predicate.
        """

        trues = []
        falses = []

        for item in self.wrapped:
            if f(item):
                trues.append(item)
            else:
                falses.append(item)

        return (trues, falses)

    def partition_map(self, pred, op_t, op_f=lambda x: x):
        """
        Applies `pred` to each element in the stream. If the result is true,
        then apply `op_t`, otherwise, apply `op_f`.
        """

        def partition_map_inner(item):
            if pred(item):
                return op_t(item)
            else:
                return op_f(item)

        return self.map(partition_map_inner)

    def fold(self, state, op):
        """
        Reduce the iterator into a single value, by way of `state = op(state, item)`
        for each element in the iterator.
        """

        for item in self.wrapped:
            state = op(state, item)

        return state

    def all(self, pred=lambda x: x):
        """
        Return true if all elements satisfy the predicate.
        Predicate defaults to the identity.
        """
        for item in self.wrapped:
            if not pred(item):
                return false
        return true

    def any(self, pred=lambda x: x):
        """
        Return true if any of the elements satisfy the predicate.
        Predicate defaults to the identity.
        """
        for item in self.wrapped:
            if pred(item):
                return true
        return false

    def none(self, pred=lambda x: x):
        """
        Return true if none of the elements satisfy the predicate.
        Predicate defaults to the identity.
        """
        for item in self.wrapped:
            if pred(item):
                return false
        return true

    def find(self, pred):
        """
        Return the first item that satisfies the predicate.
        Raise `LookupError` if not found.
        """
        for item in self.wrapped:
            if pred(item):
                return item

        raise LookupError

    def position(self, pred):
        """
        Return the position of the first item that satisfies the predicate.
        Raise `LookupError` if not found.
        """

        for (i, item) in self.enumerate():
            if pred(item):
                return i

        raise LookupError

    def rposition(self, pred):
        raise NotImplementedError

    def max(self):
        """
        Return the maximum element in the stream.
        If there are many maxima, returns the first one.
        """
        item = next(self)
        for i in self:
            if i > item:
                item = i
        return item

    def min(self):
        """
        Return the minimum element in the stream.
        If there are many minima, return the first one.
        """
        item = next(self)
        for i in self:
            if i < item:
                item = i
        return item

    def max_by_score(self, score):
        """
        Return the element with the highest score according to `score`.
        If there are many minima, returns the first one.
        """
        return self.map(score).max()

    def min_by_score(self, score):
        """
        Return the element with the lowest score according to `score`.
        If there are many minima, returns the first one.
        """
        return self.map(score).min()

    def max_by(self, comp):
        """
        `comp(a, b)` should return `True` if a is greater than b.
        Return the maximum element in the stream according to the comparison function
        given.
        If there are many maxima, returns the first one.
        """

        item = next(self)
        for i in self:
            if comp(i, item):
                item = i
        return item

    def min_by(self, comp):
        """
        `comp(a, b)` should return `True` if a is less than b.
        Return the minimum element in the stream according to the comparison function
        given.
        If there are many minima, returns the first one.
        """

        item = next(self)
        for i in self:
            if comp(i, item):
                item = i

        return item

    def unzip(self):
        """Split a stream of pairs into a pair of streams"""
        result_a = []
        result_b = []
        for (a, b) in self:
            result_a.append(a)
            result_b.append(b)

        return (result_a, result_b)

    def cycle(self):
        """Repeat this iterator endlessly."""

        class Cycle(Iterator):
            def __init__(self, wrapped):
                self.wrapped = wrapped
                self.stack = []
                self.ended = False
                self.index = 0
                self.count = 0

            def __next__(self):
                if not self.ended:
                    try:
                        self.stack.append(next(self.wrapped))
                        self.count += 1
                    except StopIteration:
                        self.ended = True

                ri = self.index % self.count
                self.index += 1
                return self.stack[ri]

        return Cycle(self)

    def sum(self):
        """
        Sum the elements of the iterator.
        Raise StopIteration if the iterator is empty.
        """
        acc = next(self)
        for item in self:
            acc += item
        return acc

    def product(self):
        """
        Return the product of all elements in the iterator.
        Raise StopIteration if the iterator is empty.
        """
        acc = next(self)
        for item in self:
            acc *= item
        return acc

    def collect(self, collector=lambda xs: [x for x in xs]):
        """
        Use ``collector`` to collect the elements of the iterator. Defaults to a
        list.

        It can be useful to pass a constructor here, to create a
        collection out of the iterator.

        Examples::
        
            `iter.collect(lambda xs: [x for x in xs])`
        
        to collect the results into a list::

            `iter.collect(lambda xs: { x[0] : x[1] for x in xs })`

        to collect stream of pairs into dictionary::

            class MyList:
                def __init__(self, stream):
                    self.items = [ i for i in stream ]

            iter.collect(MyList)

        to collect of items into my custom list type.
        """

        return collector(self)


__all__ = ["iterator", "Iterator", "into_iter"]
