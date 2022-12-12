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
    def parse_from_list(input_list: list):
        # parse all attributes but arguments
        #parsed_string = input_list.split(",")
        index, name, description, link = input_list[0], input_list[1], input_list[2], input_list[3]
        # parse arguments
        parsed_args = input_list[4:][0]

        if parsed_args == '':
            return Function(index, name, description, link, None)
        arguments = list()
        i = 0
        for arg in parsed_args.split(","):
            if "*args" in arg:
                arguments.append(Function.Argument(arg, "args", i, None))
            elif "**kwargs" in arg:
                arguments.append(Function.Argument(arg, "kwargs", i, None))
            elif "=" in arg:
                arg_name, arg_value = arg.split("=")[0], arg.split("=")[1]
                arguments.append(Function.Argument(arg_name, "hyperparameter", i, arg_value))
            else:
                arguments.append(Function.Argument(arg, "positional_argument", i, None))
            i += 1
        # create function
        function = Function(index, name, description, link, arguments)
        return function


def test():
    f = ['2202', 'pandas.read_pickle', 'Load pickled pandas object (or any object) from file.', 'https://pandas.pydata.org/docs/reference/api/pandas.read_pickle.html', "filepath_or_buffer,compression='infer',storage_options=None"]
    s = "2,pandas.HDFStore.append,Append to Table in file.,https://pandas.pydata.org/docs/reference/api/pandas.HDFStore.append.html,\"key,value,format=None,axes=None,index=True,append=True,complib=None,complevel=None,columns=None,min_itemsize=None,nan_rep=None,chunksize=None,expectedrows=None,dropna=None,data_columns=None,encoding=None,errors='strict'\""
    function = Function.parse_from_list(f)
    print(function)


test()

