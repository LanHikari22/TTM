from typing import Dict, Optional, Any
import unittest
from result import Result
import pipe

class Error:
    """
    inherit from this to create other errors
    """
    def __init__(self, msg: str, ctx: Dict) -> None:
        self.msg = msg
        self.ctx = ctx
    
    def display(self) -> str:
        return self.msg.format(**self.ctx)
    
    def __repr__(self):
        return '{Error <%s>}' % (self.ctx)


# ==================================================================================================
def parse_int(s) -> Optional[int]:
    try:
        res = int(s)
        return res
    except ValueError:
        return None

# ==================================================================================================
as_list = pipe.Pipe(list)


# ==================================================================================================
class CommonTestCase(unittest.TestCase):
    def assert_error(self, err: Result[Any, Error], exp_err_type, ctx: Dict):
        self.assertTrue(err.is_err())
        err = err.unwrap_err()
        self.assertEqual(type(err), exp_err_type)
        for k in ctx:
            self.assertTrue(k in err.ctx)
            self.assertEqual(err.ctx[k], ctx[k])