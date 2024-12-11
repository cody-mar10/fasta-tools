#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/bind_vector.h>
#include "_parser.hpp"

#define extname _fastatools

namespace nb = nanobind;

NB_MODULE(extname, m) {
    nb::class_<Record>(m, "Record")
        .def(nb::init<const std::string&, const std::string&, const std::string&>())
        .def(nb::init<const std::string&, const std::string&>())
        .def("empty", &Record::empty)
        .def("clear", &Record::clear)
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
        .def("next", &Parser::next);
}