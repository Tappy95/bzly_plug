from models.alchemy_models import *

print(type(t_tp_ibx_callback))
print(type(t_tp_xw_callback))
a = type(t_tp_ibx_callback) == type(t_tp_xw_callback)
print(a)
