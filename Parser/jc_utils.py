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

def int_to_alph(i):
    if i <= 0:
        raise Exception("Argument needs to be positive")
    else:
        ret = ""
        while i > 0:
            r = (i - 1) % 26
            ret = chr(ord('a') + r) + ret
            i = (i - 1)/ 26
        return ret
