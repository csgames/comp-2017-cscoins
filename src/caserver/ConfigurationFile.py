import os
import decimal

class ConfigurationFile(object):
    def __init__(self, filename="ca_config.txt"):
        self.filename = filename
        self.vars = {}
        
    def read_file(self):
        if not os.path.exists(self.filename):
            return

        fp = open(self.filename, 'r')
        lines = fp.readlines()

        for l in lines:
            data = l.split('=')
            if len(data) >= 2:
                var = data[0].lstrip().rstrip()
                value = data[1].lstrip().rstrip()

                self.vars[var] = value

        fp.close()

    def __get_int(self, var_name):
        return int(self.vars[var_name])

    def get_int(self, var_name, default_value):
        try:
            return self.__get_int(var_name)
        except:
            return default_value

    def __get_int_tuple(self, var_name):
        tuple = self.__get_string(var_name)
        int_tuple = []
        elements = tuple.split(',')
        for elem in elements:
            value = elem.lstrip().rstrip()
            int_tuple.append(int(value))
        return int_tuple

    def get_int_tuple(self, var_name, default_value):
        try:
            return self.__get_int_tuple(var_name)
        except:
            return default_value

    def __get_string(self, var_name):
        return self.vars[var_name]

    def get_string(self, var_name, default_value):
        try:
            return self.__get_string(var_name)
        except:
            return default_value

    def __get_float(self, var_name):
        return float(self.vars[var_name])

    def get_float(self, var_name, default_value):
        try:
            return self.__get_float(var_name)
        except:
            return default_value

    def __get_decimal(self, var_name):
        return decimal.Decimal(self.vars[var_name])

    def get_decimal(self, var_name, default_value):
        try:
            return self.__get_decimal(var_name)
        except:
            return default_value

    def __get_bool(self, var_name):
        if self.vars[var_name] == 'True':
            return True
        else:
            return False

    def get_bool(self, var_name, default_value):
        try:
            return self.__get_bool(var_name)
        except:
            return default_value

    def __get_string_tuple(self, var_name, separator=','):
        string_tuple = self.__get_string(var_name).split(separator)
        return string_tuple

    def get_string_tuple(self, var_name, default_value, separator=','):
        try:
            return self.__get_string_tuple(var_name, separator)
        except:
            return default_value