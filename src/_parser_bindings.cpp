#include <string>
#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/bind_vector.h>
#include "_parser.hpp"

#define extname _fastatools

namespace nb = nanobind;

/*
Python wrapper for `next()` that raises a Python `StopIteration` exception when the end of the file is reached.
*/
Record Parser::py_next() {
    if (this->file.eof()) {
        throw nb::stop_iteration();
    }

    Record record = this->next();

    if (record.empty()) {
        throw nb::stop_iteration();
    }

    return record;
}

NB_MODULE(extname, m) {
    nb::class_<Record>(m, "Record")
        .def(nb::init<const std::string&, const std::string&, const std::string&>())
        .def(nb::init<const std::string&, const std::string&>())
        .def(nb::self == nb::self)
        .def(nb::self != nb::self)
        .def("empty", &Record::empty)
        .def("clear", &Record::clear)
        .def("to_string", &Record::to_string)
        .def("header", &Record::header)
        .def_rw("name", &Record::name)
        .def_rw("desc", &Record::desc)
        .def_rw("seq", &Record::seq);

    nb::bind_vector<Records>(m, "Records");

    nb::class_<Parser>(m, "Parser")
        .def(nb::init<const std::string&>())
        .def("has_next", &Parser::has_next)
        .def("all", &Parser::all)
        .def("take", &Parser::take)
        .def("refresh", &Parser::refresh)
        .def("next", &Parser::next)
        .def("py_next", &Parser::py_next);
}