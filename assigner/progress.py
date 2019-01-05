import enlighten

# prevent name shadowing
__enumerate = enumerate

def iterate(iterable):
    return Progress(iterable)

def enumerate(iterable):
    return __enumerate(iterate(iterable))

class Progress:
    def __init__(self, iterable):
        try:
            total = len(iterable)
        except (TypeError, AttributeError):
            total = None

        self.iterable = iterable
        self.manager = enlighten.get_manager()
        self.pbar = self.manager.counter(total=total)

    def __iter__(self):
        for item in self.iterable:
            yield item
            self.pbar.update()
        self.manager.stop()
