.. iterator documentation master file, created by
   sphinx-quickstart on Sat Nov 24 17:28:47 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

``iterator``: Rust-inspired iteration
==========================================

This library provides the :class:`~iterator.Iterator` type, directly inspired by the 
`trait <https://doc.rust-lang.org/std/iter/index.html>`_ of the same name in Rust.

The easiest way to use this is to use :func:`~iterator.into_iter`, which produces an
:class:`~iterator.Iterator` from any iterable. Most of the methods provided by the
Rust trait are present here too.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   iterator/iterator

Examples
--------

Basic usage::

   import iterator
   result = iterator.into_iter(range(5)).map(lambda x: 2*x).collect()
   assert result = [2, 4, 6, 8, 10]

You can use :class:`~iterator.Iterator` anywhere an iterable is expected::

   for i in into_iter(range(5)).map(lambda x: 2*x):
      print(i)

Indices and tables
------------------

* :ref:`genindex`
* :ref:`search`
