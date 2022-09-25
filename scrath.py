import re

string = 'THC:�13.099%��|��CBD:�9.809%'

string = string.split('%')
string = string[0]
print(string)
non_decimal = re.compile(r'[^\d.]+')
string = float(non_decimal.sub('', string))
print(string)
