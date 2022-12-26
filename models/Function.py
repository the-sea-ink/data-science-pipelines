import sqlite3


class Function:
    class Argument:

        def __init__(self, name, type, position, default_value):
            self.name = name
            self.type = type
            self.position = position
            self.default_value = default_value

        def __str__(self):
            if self.type == "hyperparameter":
                return self.name + "=" + self.default_value
            else:
                return self.name

        def __repr__(self):
            return self.__str__()

    def __init__(self, name, description, link, args):
        self.name = name
        self.description = description
        self.link = link
        self.args = args

    def __str__(self):
        return f'{self.name}, {self.description}, {self.link}\n args: {self.args}'

    @staticmethod
    def parse_from_list(input_list: list):
        # extract all attributes but arguments
        name, description, link = input_list[0], input_list[1], input_list[2]
        # extract arguments
        parsed_args = input_list[3:][0]

        if parsed_args == '':
            return Function(name, description, link, None)
        arguments = list()
        i = 0
        for arg in parsed_args.split(","):
            if "=" in arg:
                arg_name, arg_value = arg.split("=")[0], arg.split("=")[1]
                arguments.append(Function.Argument(arg_name, "hyperparameter", i, arg_value))
            elif "*args" in arg or arg == "*":
                arguments.append(Function.Argument(arg, "args", i, None))
            elif "**" in arg:
                arguments.append(Function.Argument(arg, "kwargs", i, None))
            else:
                arguments.append(Function.Argument(arg, "positional_argument", i, None))
            i += 1
        # create function
        function = Function(name, description, link, arguments)
        return function

    @staticmethod
    def parse_from_db(cursor, module_name, title):
        cursor.execute(
            "SELECT function_id, module_name, function_title, description, link FROM functions WHERE module_name = ? AND function_title =?",
            (module_name, title))
        func = cursor.fetchall()
        func_id = func[0][0]
        cursor.execute(
            "SELECT argument_name, argument_type, argument_position, default_value FROM arguments WHERE function_id = ?",
            (func_id,))
        args = cursor.fetchall()
        if len(args) == 0 and len(func) != 0:
            return Function(func[0][1], func[0][2], func[0][3],  None)
        elif len(func) != 0:
            arguments = []
            for arg in args:
                if arg[1] != "hyperparameter":
                    arguments.append(Function.Argument(arg[0], arg[1], arg[2], None))
                else:
                    arguments.append(Function.Argument(arg[0], arg[1], arg[2], arg[3]))
        if len(func) != 0:
            function = Function(func[0][1], func[0][2], func[0][3], arguments)
            return function
        return -1


def test():
    f = ['pandas.read_pickle', 'Load pickled pandas object (or any object) from file.',
         'https://pandas.pydata.org/docs/reference/api/pandas.read_pickle.html',
         "filepath_or_buffer,compression='infer',storage_options=None"]
    s = "pandas.HDFStore.append,Append to Table in file.,https://pandas.pydata.org/docs/reference/api/pandas.HDFStore.append.html,\"key,value,format=None,axes=None,index=True,append=True,complib=None,complevel=None,columns=None,min_itemsize=None,nan_rep=None,chunksize=None,expectedrows=None,dropna=None,data_columns=None,encoding=None,errors='strict'\""
    function = Function.parse_from_list(f)
    print(function)

test()
