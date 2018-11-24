"""
A lazy iterator type inspired by Rust's iterator types.

You can extend your own types to use this iterator interface by inheriting
from the Iterator class and overriding the __next__ method.

You can also use the `into_iter` function, which accepts any Python iterable
and returns an Iterator.
"""

from joblib import Parallel, delayed

def into_iter(iterable):
    """Creates an Iterator from the iterable."""

    class IntoIterator(Iterator):
        def __init__(self, iterable):
            self.wrapped = iterable

        def __next__(self):
            return next(self.wrapped)

    return IntoIterator(iter(iterable))


class Iterator:
    """A lazy iterator type inspired by Rust iterators."""

    def __iter__(self):
        """Return self."""
        return self

    def __next__(self):
        """
        Return the next value in the iterator.

        You should override this method; the default is to simply raise StopIteration.
        """
        raise StopIteration

    def count(self):
        """Consume the iterator, counting the number of iterations and returning it."""
        counter = 0
        for i in self:
            counter += 1

        return counter

    def last(self):
        """Return the last item in the iterator. Return None if the iterator is empty."""
        item = None
        for i in self:
            item = i

        return item

    def filter(self, pred):
        """Return a stream of values for which the predicate is true."""

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
        """Flatten nested structure."""

        class Flatten(Iterator):
            def __init__(self, wrapped):
                self.wrapped = wrapped
                self.current = next(self.wrapped)

            def __next__(self):
                try:
                    return next(self.current)
                except StopIteration:
                    self.current = next(self.wrapped)
                    return next(self)

        return Flatten(self)

    def map(self, op):
        """Return a stream of `op` applied to each element."""

        class Map(Iterator):
            def __init__(self, wrapped, op):
                self.wrapped = wrapped
                self.op = op

            def __next__(self):
                return self.op(next(self.wrapped))

        return Map(self, op)

    def flat_map(self, op):
        """
        Where `op` returns a stream of items, apply `op` to each element
        of the iterator and flatten the resulting nested structure.
        """

        return self.map(op).flatten()

    def filter_map(self, op):
        """
        `op` should return `(bool, item)`. If bool is false, skips item.
        """

        class FilterMap(Iterator):
            def __init__(self, wrapped, op):
                self.wrapped = wrapped
                self.op = op

            def __next__(self):
                (p, item) = self.op(next(self.wrapped))
                if p:
                    return item
                else:
                    return next(self)

        return FilterMap(self, op)

    def zip(self, other):
        """Return a stream of pairs from a pair of streams."""

        class Zip(Iterator):
            def __init__(self, wrapped, other):
                self.wrapped = wrapped
                self.other = other

            def __next__(self):
                return (next(self.wrapped), next(self.other))

        return Zip(self, other)

    def chain(self, other):
        """Return a stream of values from `self`, then from `other`."""

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
        essentially does

            [ f(x) for x in xs ]

        Compare to this method, which essentially does

            [ (f(x), x)[1] for x in xs ]

        In other words, `map` applies a function to each element of the iterator
        and returns the *result*, `inspect` applies a function to each element of
        the iterator and returns *the element*.

        This can be useful e.g for logging errors before filtering them out.

            def log_if_bad(egg):
                if egg.is_bad():
                    print("bad egg will be removed")
                else:
                    pass

            my_iter\
            .map(lambda x: some_operation(x))\
            .inspect(lambda e: log_if_bad(e))\
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
        Consume the iterater, splitting the elements into two lists based
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

    def all(self, pred):
        """Return true if all elements satisfy the predicate."""
        for item in self.wrapped:
            if not pred(item):
                return false
        return true

    def any(self, pred):
        """Return true if any of the elements satisfy the predicate."""
        for item in self.wrapped:
            if pred(item):
                return true
        return false

    def none(self, pred):
        """Return true if none of the elements satisfy the predicate."""
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
        Use collector to collect the elements of the iterator.
        It can be useful to pass a constructor here, to create a
        collection out of the iterator.

        Examples:
        
            `iter.collect(lambda xs: [x for x in xs])`
        
        to collect the results into a list

            `iter.collect(lambda xs: { x[0] : x[1] for x in xs })`

        to collect stream of pairs into dictionary.

            class MyList:
                def __init__(self, stream):
                    self.items = [ i for i in stream ]

            iter.collect(MyList)

        to collect of items into my custom list type.
        """

        return collector(self)

    def par_collect(self):
        """
        Use `joblib` to collect the results into a list in parallel.

        Note that this is done by spawning a number of Python subprocesses, so
        unless you have quite a bit of computation to do, this might actually
        be slower.
        """
        return Parallel(n_jobs=-1)(delayed(lambda x: x)(i) for i in self)


__all__ = [ "iterator", "Iterator", "into_iter"]
