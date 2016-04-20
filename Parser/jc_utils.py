def unique(seq, idfun=None): # Order preserving
  return list(_unique(seq, idfun))

def _unique(seq, idfun=None):  
  ''' Originally proposed by Andrew Dalke '''
  seen = set()
  if idfun is None:
    for x in seq:
      if x not in seen:
        seen.add(x)
        yield x
  else:
    for x in seq:
      x = idfun(x)
      if x not in seen:
        seen.add(x)
        yield x
