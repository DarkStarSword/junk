#!/usr/bin/env python2.6
# vi:sw=2:ts=2:expandtab

class ui_null(object):
  """
  Dummy class that will do nothing when called, and return itself as any of
  it's attributes.  Intended to be used in place of a ui class where no
  interaction is to take place. Calls such as ui_null().mainloop.foo.bar.baz()
  will not raise any exceptions.
  """
  def __call__(self, *args): pass
  def __getattribute__(self,name):
    return self

