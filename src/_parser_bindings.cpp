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

/*
Python wrapper for `next_header()` that raises a Python `StopIteration` exception when the end of the file is reached.
*/
Header Parser::py_next_header() {
    if (this->file.eof()) {
        throw nb::stop_iteration();
    }

    Header header = this->next_header();

    if (header.empty()) {
        throw nb::stop_iteration();
    }

    return header;
}

NB_MODULE(extname, m) {
    nb::class_<Header>(m, "Header")
        .def(nb::init<const std::string&, const std::string&>())
        .def(nb::init<const std::string&>())
        .def(nb::self == nb::self)
        .def(nb::self != nb::self)
        .def("empty", &Header::empty)
        .def("clear", &Header::clear)
        .def("clean", &Header::clean)
        .def("to_string", &Header::to_string)
        .def_rw("name", &Header::name)
        .def_rw("desc", &Header::desc)
        ;

    nb::class_<Record>(m, "Record")
        .def(nb::init<const std::string&, const std::string&, const std::string&>())
        .def(nb::init<const std::string&, const std::string&>())
        .def(nb::self == nb::self)
        .def(nb::self != nb::self)
        .def("empty", &Record::empty)
        .def("clear", &Record::clear)
        .def("clean_header", &Record::clean_header)
        .def("remove_stops", &Record::remove_stops)
        .def("to_string", &Record::to_string)
        .def_rw("header", &Record::header)
        .def_rw("seq", &Record::seq)
        .def_rw("type", &Record::type)
        ;

    nb::bind_vector<Records>(m, "Records");
    nb::bind_vector<Headers>(m, "Headers");

    nb::enum_<RecordType>(m, "RecordType")
        .value("GENOME", RecordType::GENOME)
        .value("GENE", RecordType::GENE)
        .value("PROTEIN", RecordType::PROTEIN)
        .value("NUCLEOTIDE", RecordType::NUCLEOTIDE)
        .value("UNKNOWN", RecordType::UNKNOWN)
        .export_values()
        ;

    nb::class_<Parser>(m, "Parser")
        .def(nb::init<const std::string&>())
        .def("has_next", &Parser::has_next)
        .def("all", &Parser::all)
        .def("take", &Parser::take)
        .def("refresh", &Parser::refresh)
        .def("next", &Parser::next)
        .def("py_next", &Parser::py_next)
        .def("count", &Parser::count)
        .def("extension", &Parser::extension)
        .def("next_header", &Parser::next_header)
        .def("py_next_header", &Parser::py_next_header)
        .def("headers", &Parser::headers)
        .def_rw("type", &Parser::type)
        ;
}