from pyparsing import alphanums, Word, Optional, Char, ZeroOrMore, Literal, restOfLine, SkipTo, LineStart, OneOrMore
from typing import List, Any
import typing as tp
import os

THE_TAB = "    "


def check_is_normal_visibility(param: str, is_private: bool) -> bool:
    if (param[:2] == "__" and is_private) or (param[:2] != "__" and not is_private):
        return True
    else:
        raise Exception("wrong visibility")


class Parameter:
    __the_name: str
    __the_type: tp.Optional[str] = None
    __std_value: tp.Optional[str] = None

    def __init__(self, the_name: str, the_type: tp.Optional[str], std_value: tp.Optional[str]):
        self.__the_name = the_name
        self.__the_type = the_type
        self.__std_value = std_value

    def to_string(self) -> str:
        return "parameter: {" + "name: " + self.__the_name + ", type: " + str(self.__the_type) + ", std_value: " + str(
            self.__std_value) + "}"

    def to_file(self):
        std_type = ": " + self.__the_type if self.__the_type is not None else ""
        std_value = " = " + self.__std_value if self.__std_value is not None else ""
        return self.__the_name + std_type + std_value


class Method:
    __the_name: str
    __is_private: bool
    __return_type: str
    __parameters: List[Parameter]

    def __init__(self, the_name: str, is_private: bool, return_type: str, parameters: List[Parameter]):
        check_is_normal_visibility(the_name, is_private)
        self.__the_name = the_name
        self.__is_private = is_private
        self.__return_type = return_type
        self.__parameters = parameters

    def to_string(self) -> str:
        str_parameters = ""
        for parameter in self.__parameters:
            str_parameters += "\n\t\t" + parameter.to_string()
        return "method: {" + "name: " + self.__the_name + ", is_private: " + str(
            self.__is_private) + ", return_type: " + str(self.__return_type) + ", parameters: " + str_parameters + "}"

    def to_file(self):
        string_parameters = ""
        for parameter in self.__parameters:
            string_parameters += parameter.to_file() + ", "
        if len(self.__parameters) != 0:
            string_parameters = string_parameters[:-2]
        return_type = " -> " + self.__return_type if self.__return_type != "void" else ""
        return "\n" + THE_TAB + "def " + self.__the_name + "(" + string_parameters + ")" + return_type \
               + ":\n" + THE_TAB * 2 + "pass\n"


class Attribute:
    __the_name: str
    __is_private: bool
    __the_type: str
    __std_value: tp.Optional[str] = None

    def __init__(self, the_name: str, is_private: bool, the_type: str, std_value: tp.Optional[str]):
        check_is_normal_visibility(the_name, is_private)
        self.__the_name = the_name
        self.__is_private = is_private
        self.__the_type = the_type
        self.__std_value = std_value

    @property
    def is_private(self) -> bool:
        return self.__is_private

    def is_set_std_value(self):
        return self.__std_value is not None

    def to_string(self) -> str:
        return "attribute: {" + "name: " + self.__the_name + ", is_private: " + str(
            self.__is_private) + ", type: " + str(self.__the_type) + ", std_value: " + str(self.__std_value) + "}"

    def to_file(self) -> str:
        return THE_TAB + self.__the_name + ": " + self.__the_type

    def to_init_param(self) -> str:
        if not self.__is_private:
            raise Exception("only private attribute to init")
        std_value = ""
        if self.__std_value is not None:
            std_value = " = " + self.__std_value
        return self.__the_name[2:] + ": " + self.__the_type + std_value

    def to_init_set(self) -> str:
        if not self.__is_private:
            raise Exception("only private attribute to init set")
        return THE_TAB * 2 + "self." + self.__the_name + " = " + self.__the_name[2:]

    def to_file_getter(self) -> str:
        if not self.__is_private:
            raise Exception("only private attribute to getter")
        return "\n" + THE_TAB + "@property\n" + THE_TAB + "def " + self.__the_name[2:] + "(self) -> " \
               + self.__the_type + ":\n" + THE_TAB * 2 + "return self." + self.__the_name + "\n"

    def to_file_setter(self) -> str:
        if not self.__is_private:
            raise Exception("only private attribute to setter")
        return "\n" + THE_TAB + "@" + self.__the_name[2:] + ".setter\n" + THE_TAB + "def " + self.__the_name[2:] \
               + "(self, " + self.__the_name[2:] + ": " + self.__the_type + "):\n" + THE_TAB * 2 + "self." \
               + self.__the_name + " = " + self.__the_name[2:] + "\n"


class TheImport:
    __base_package: tp.Optional[str]
    __the_name: str
    __is_remote: bool
    __rename: tp.Optional[str] = None

    def __init__(self, full_name: str):
        self.__is_remote = full_name[0] == "$"
        if self.__is_remote:
            full_name = full_name[1:]
        split_name = full_name.split(".")
        space = 0
        if split_name[-1].startswith("__") and split_name[-1].endswith("__"):
            self.__rename = split_name[-1][2:-2]
            space = 1
        if len(split_name) - space > 1:
            base_package = ""
            for i in range(len(split_name) - 1 - space):
                base_package += split_name[i] + "."
            self.__base_package = base_package[:-1]
        else:
            self.__base_package = None
        self.__the_name = split_name[-1 - space]

    @property
    def parent(self) -> str:
        return self.__the_name

    def to_string(self) -> str:
        base_package = ""
        if self.__base_package is not None:
            base_package = " from " + str(self.__base_package)
        rename = ""
        if self.__rename is not None:
            rename = " as " + self.__rename
        return base_package + " import " + self.__the_name + rename

    def to_file(self) -> str:
        base_package = ""
        if self.__is_remote and self.__base_package is not None:
            base_package = "from " + str(self.__base_package) + " "
        elif not self.__is_remote:
            bp = "" if self.__base_package is None else self.__base_package + "."
            base_package = "from " + bp + self.__the_name[0].lower() + self.__the_name[1:] + " "
        rename = ""
        if self.__rename is not None:
            rename = " as " + self.__rename
        return base_package + "import " + self.__the_name + rename


class TheClass:
    __full_class_name: str
    __parent: tp.Optional[str] = None
    __attributes: List[Attribute]
    __methods: List[Method]
    __imports: List[TheImport]

    def __init__(self, full_class_name: str, attributes: List[Attribute], methods: List[Method]):
        self.__imports = list()
        self.__full_class_name = full_class_name
        self.__attributes = attributes
        self.__methods = methods

    @property
    def full_class_name(self) -> str:
        return self.__full_class_name

    @property
    def parent(self) -> str:
        return self.__parent

    @parent.setter
    def parent(self, parent):
        self.__parent = parent

    def get_normal_name(self) -> str:
        split_name = self.__full_class_name.split(".")
        space = 0
        if split_name[-1].startswith("__") and split_name[-1].endswith("__"):
            space = 1
        nn = split_name[-1 - space]
        if nn.startswith("$"):
            return nn[1:]
        else:
            return nn

    def get_normal_base(self) -> str:
        split_name = self.__full_class_name.split(".")
        space = 0
        if split_name[-1].startswith("__") and split_name[-1].endswith("__"):
            space = 1
        base = split_name[:-1 - space]
        str_base = ""
        for b in base:
            bb = b[1:] if b.startswith("$") else b
            str_base += bb + "/"
        return str_base

    def add_import(self, the_import: TheImport):
        self.__imports.append(the_import)

    def get_file_name(self) -> str:
        nn = self.get_normal_name()[0].lower() + self.get_normal_name()[1:]
        return self.get_normal_base() + nn + ".py"

    def to_string(self):
        parent = ""
        if self.__parent is not None:
            parent = self.__parent
        imports = ""
        for the_import in self.__imports:
            imports += "\n" + the_import.to_string()
        str_attributes = ""
        for attribute in self.__attributes:
            str_attributes += "\n\t" + attribute.to_string()
        str_methods = ""
        for method in self.__methods:
            str_methods += "\n\t" + method.to_string()
        return "class: {" + imports + "\nname: " + self.get_normal_name() + "(" + parent + ")" + ", attributes: { " \
               + str_attributes + " }, methods: { " + str_methods + "} }"

    def __get_attributes_to_file(self) -> str:
        string = ""
        for attribute in self.__attributes:
            string += "\n" + attribute.to_file()
        return string

    def __get_init_to_file(self) -> str:
        string = "\n" + THE_TAB + "def __init__(self, "
        string2 = ""
        for attribute in self.__attributes:
            if attribute.is_private and not attribute.is_set_std_value():
                string += attribute.to_init_param() + ", "
                string2 += "\n" + attribute.to_init_set()
        for attribute in self.__attributes:  # attributes with std_value must be in the end
            if attribute.is_private and attribute.is_set_std_value():
                string += attribute.to_init_param() + ", "
                string2 += "\n" + attribute.to_init_set()
        string = string[:-2]
        if len(self.__attributes) == 0:
            return string + "):\n" + THE_TAB * 2 + "pass"
        else:
            return string + "):" + string2 + "\n"

    def __get_getters_and_setters_to_file(self) -> str:
        string = ""
        for attribute in self.__attributes:
            if attribute.is_private:
                string += attribute.to_file_getter()
                string += attribute.to_file_setter()
        return string

    def __get_methods_to_file(self) -> str:
        string = ""
        for method in self.__methods:
            string += method.to_file()
        return string

    def to_file(self) -> tp.Optional[str]:
        if self.__full_class_name.startswith("$"):
            return None
        imports = ""
        for the_import in self.__imports:
            imports += the_import.to_file() + "\n"
        if imports != "":
            imports += "\n\n"
        parent = ""
        if self.__parent is not None:
            parent = "(" + self.__parent + ")"
        return imports + "class " + self.get_normal_name() + parent + ":" + self.__get_attributes_to_file(
        ) + "\n" + self.__get_init_to_file() + self.__get_getters_and_setters_to_file(
        ) + self.__get_methods_to_file() + "\n"


def get_method_params(method_params: str) -> List[List[str]]:
    parameter_name = alphanums + "_"
    parameter_type = alphanums + "_.[]"
    parameter_value = alphanums + "_.[]()"
    parameter = (Word(parameter_name) + Optional(Char(":") + Word(parameter_type)) + Optional(
        Char("=") + Word(parameter_value))).setResultsName("params", listAllMatches=True)
    parse_method = ZeroOrMore(parameter + Optional(Char(",")))
    return parse_method.parseString(method_params).params


def get_class_parser(class_body: str) -> Any:
    attribute_name = alphanums + "_"
    parameter_type = alphanums + "_.[]"
    parameter_value = alphanums + "_.[]()"
    method_name = alphanums + "_"
    method_return = alphanums + "_.[]"
    comment = (Literal("'") + restOfLine()).suppress()

    attribute = (Char("+-") + Word(attribute_name) + Char(":").suppress() + Word(parameter_type) + Optional(
        Char("=").suppress() + Word(parameter_value))).setResultsName("attributes", listAllMatches=True)

    method = (Char("+-") + Word(method_name) + Char("(").suppress() + SkipTo(")") + Char(")").suppress() + Char(
        ":").suppress() + Word(method_return)).setResultsName("methods", listAllMatches=True)

    parse_class_body = ZeroOrMore(attribute | method | comment)
    return parse_class_body.parseString(class_body)


def get_file_parser(file_name: str) -> Any:
    the_class_name = alphanums + "_.$"
    start_file = (Literal("@startuml"))
    hide_setting = (Literal("hide") + Literal("empty") + Literal("members")).suppress()
    base_class = (LineStart().suppress() + Literal("class").suppress() + Word(the_class_name) + Literal(
        "{").suppress() + SkipTo("}") + Literal("}").suppress()).setResultsName("classes", listAllMatches=True)
    comment = (Literal("'") + restOfLine()).suppress()
    relationship = (LineStart().suppress() + Word(the_class_name) + Word("-|>*.<o") + Word(
        the_class_name) + restOfLine().suppress()).setResultsName("relationships", listAllMatches=True)
    note = (LineStart().suppress() + Literal("note") + restOfLine).suppress()
    end_file = (SkipTo("@enduml").suppress() + Literal("@enduml"))

    parse_file = start_file + hide_setting + OneOrMore(base_class | comment | relationship | note) + end_file
    return parse_file.parseFile(file_name)


def create_class_list(filename: str) -> List[TheClass]:
    parser = get_file_parser(filename)

    class_list = []
    for the_class in parser.classes:
        class_body = get_class_parser(the_class[1])
        list_attribute = []
        for attribute in class_body.attributes:
            std_value = attribute[3] if len(attribute) == 4 else None
            list_attribute.append(Attribute(attribute[1], attribute[0] == "-", attribute[2], std_value))
        list_method = []
        for the_method in class_body.methods:
            list_param = []
            for method_param in get_method_params(the_method[2]):
                the_type, the_value = None, None
                if len(method_param) > 2:
                    if method_param[1] == ":":
                        the_type = method_param[2]
                    else:
                        raise Exception("all must have the type")
                    if len(method_param) > 4:
                        the_value = method_param[4]
                list_param.append(Parameter(method_param[0], the_type, the_value))
            list_method.append(Method(the_method[1], the_method[0] == "-", the_method[3], list_param))
        class_list.append(TheClass(the_class[0], list_attribute, list_method))

    for the_relationship in parser.relationships:
        if the_relationship[1] == "<.." or the_relationship[1] == "--o" or the_relationship[1] == "--*":
            for my_class in class_list:
                if my_class.full_class_name == the_relationship[2]:
                    my_class.add_import(TheImport(the_relationship[0]))
        elif the_relationship[1] == "<|--":
            for my_class in class_list:
                if my_class.full_class_name == the_relationship[2]:
                    parent_import = TheImport(the_relationship[0])
                    my_class.add_import(parent_import)
                    my_class.parent = parent_import.parent
        else:
            raise Exception("unknown relationship")

    return class_list


def main():
    in_file = input("Enter '.puml' file (empty to ./all_example_classes.puml):\n")
    if in_file == "":
        in_file = "./all_example_classes.puml"
    classes = create_class_list(in_file)
    out_dir = input("Enter output dir (empty to ./out/):\n")
    if out_dir == "":
        out_dir = "./out/"
    for the_class in classes:
        class_file = the_class.to_file()
        if class_file is not None:
            print("write class " + the_class.get_normal_name() + " to " + out_dir + the_class.get_file_name())
            if not os.path.exists(out_dir + the_class.get_normal_base()):
                os.makedirs(out_dir + the_class.get_normal_base())
            with open(out_dir + the_class.get_file_name(), "w") as file:
                file.write(the_class.to_file())


if __name__ == '__main__':
    main()
