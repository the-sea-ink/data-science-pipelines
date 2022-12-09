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

    def __init__(self, index, name, description, link, args):
        self.index = index
        self.name = name
        self.description = description
        self.link = link
        self.args = args


    def __str__(self):
        return f'{self.index}, {self.name}, {self.description}, {self.link}\n args: {self.args}'

    @staticmethod
    def parse_from_string(input_string: str):
        # parse all attributes but arguments
        parsed_string = input_string.split(",")
        index, name, description, link = parsed_string[0], parsed_string[1], parsed_string[2], parsed_string[3]
        # parse arguments
        parsed_args = parsed_string[4:]
        # strip " at start and end of argument list
        parsed_args[0] = parsed_args[0][1:]
        parsed_args[-1] = parsed_args[-1][:-1]
        arguments = list()
        for arg in parsed_args:
            if "*args" in arg:
                arguments.append(Function.Argument(arg, "args", parsed_args.index(arg), None))
            elif "**kwargs" in arg:
                arguments.append(Function.Argument(arg, "kwargs", parsed_args.index(arg), None))
            elif "=" in arg:
                arg_name, arg_value = arg.split("=")[0], arg.split("=")[1]
                arguments.append(Function.Argument(arg_name, "hyperparameter", parsed_args.index(arg), arg_value))
            else:
                arguments.append(Function.Argument(arg, "positional_argument", parsed_args.index(arg), None))
        # create function
        function = Function(index, name, description, link, arguments)
        return function

def test():
    s = "2,pandas.HDFStore.append,Append to Table in file.,https://pandas.pydata.org/docs/reference/api/pandas.HDFStore.append.html,\"key,value,format=None,axes=None,index=True,append=True,complib=None,complevel=None,columns=None,min_itemsize=None,nan_rep=None,chunksize=None,expectedrows=None,dropna=None,data_columns=None,encoding=None,errors='strict'\""
    function = Function.parse_from_string(s)
    print(function)

test()
