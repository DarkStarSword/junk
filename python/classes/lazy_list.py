class lazy_list():
  """
  Convert input into a list like object in the background or on demand.

  Useful when processing data that is going to take time to load, but we want
  to start processing immediately, and are able to process the input mostly
  linearly (accessing the last element would defeat this).

  Note: If you apply a transformation to the result of this list you will
  end up defeating the point of using it. It is better to apply the
  transformation to the INPUT to this class by passing in a generator function
  that applies the transformation as we request the entries. If you really do
  need to transform the output, consider doing so in a lazy fashion.

  Note: This doesn't implement everything we need to be a full duck typed list,
  and I don't want to subclass, because then a bunch of things would appear to
  work that in reality don't without overriding them anyway (index, len, etc.).
  It's better to add functionality as we need it.
  """
  def __init__(self, input):
    import threading

    self._list = []
    self._done = False
    t = threading.Thread(target=self._worker, args=[input])
    t.daemon = True # Don't prevent termination
    t.start()

  def _worker(self, input):
    for x in input:
      self._list.append(x)
    self._done = True

  def __getitem__(self, idx):
    while not self._done:
      try:
        return self._list[idx]
      except IndexError:
        import time
        time.sleep(0.5)
    return self._list[idx]
