#ifndef _PARSER_HPP
#define _PARSER_HPP

#include <fstream>
#include <string>
#include <tuple>
#include <vector>
#include <iostream>
#include <nanobind/nanobind.h>

#define SEQLINESIZE 75
#define MAXHEADERLEN 150
struct Record {
    using Header = std::pair<std::string, std::string>;

private:
    std::string data;

    inline Header split(const std::string& name) {

        std::size_t space_pos = name.find(' ');

        if (space_pos == std::string::npos) {
            return std::make_pair(name, "");
        }

        return std::make_pair(name.substr(0, space_pos), name.substr(space_pos + 1));
    }


    inline void read(std::istream& is, std::string& bufline) {
        if (bufline.empty()) {
            std::getline(is, bufline);
        }

        if (bufline[0] != '>') {
            // should throw an error but what if EOF?
            return;
        }

        Header header = this->split(bufline);

        while (std::getline(is, bufline)) {
            if (bufline.empty()) {
                continue;
            }

            // at next record
            if (bufline[0] == '>') {
                break;
            }

            this->seq += bufline;
        }

        // remove > symbol from beginning of name
        // BUG: if the header is just > without a name?
        this->name = std::move(header.first.substr(1));
        this->desc = std::move(header.second);
    }

public:
    std::string name;
    std::string desc;
    std::string seq;

    // default constructor
    Record() : name(""), desc(""), seq("") {}

    // copy constructor
    Record(const Record& other) : name(other.name), desc(other.desc), seq(other.seq) {}

    // copy constructor with all 3 fields precomputed
    Record(const std::string& name, const std::string& desc, const std::string& seq) : name(name), desc(desc), seq(seq) {}

    // copy constructor that will split `name` at the first space into an actual name and description
    Record(const std::string& name, const std::string& seq) {
        std::pair<std::string, std::string> split_name = split(name);
        this->name = split_name.first;
        this->desc = split_name.second;
        this->seq = seq;
    }

    // move constructor with all 3 fields precomputed
    Record(std::string&& name, std::string&& desc, std::string&& seq) : name(std::move(name)), desc(std::move(desc)), seq(std::move(seq)) {}

    // move constructor that will split `name` at the first space into an actual name and description
    Record(std::string&& name, std::string&& seq) {
        std::string local_name = std::move(name);
        std::pair<std::string, std::string> split_name = split(local_name);
        this->name = std::move(split_name.first);
        this->desc = std::move(split_name.second);
        this->seq = std::move(seq);
    }

    // constructor that reads from a stream
    Record(std::istream& is, std::string& bufline) {
        this->read(is, bufline);
    }

    inline bool empty() {
        return this->name.empty() && this->desc.empty() && this->seq.empty();
    }

    inline void clear() {
        this->name.clear();
        this->desc.clear();
        this->seq.clear();
    }

    std::string to_string() const {
        std::string str_record;
        size_t num_seq_lines = this->seq.size() / SEQLINESIZE + 1;

        str_record.reserve(this->seq.size() + MAXHEADERLEN + num_seq_lines);

        str_record += this->header();
        str_record += '\n';

        for (size_t i = 0; i < this->seq.size(); i += SEQLINESIZE) {
            str_record += this->seq.substr(i, SEQLINESIZE);
            str_record += '\n';
        }

        return str_record;
    }

    std::string header() const {
        std::string str;
        str.reserve(this->name.size() + this->desc.size() + 10);
        str += this->name;

        if (!this->desc.empty()) {
            str += ' ';
            str += this->desc;
        }

        return str;
    }

    friend std::ostream& operator<<(std::ostream& os, const Record& record) {
        return os << record.to_string();
    }

    bool operator==(const Record& other) const {
        return this->name == other.name && this->desc == other.desc && this->seq == other.seq;
    }

    bool operator!=(const Record& other) const {
        return !(*this == other);
    }

};

using Records = std::vector<Record>;

class Parser {
private:
    std::ifstream file;
    std::string line;

    inline void setup_file(const std::string& filename) {
        this->file.open(filename);
        if (!this->file.good()) {
            throw std::runtime_error("Could not open file: " + filename);
        }
        else {
            this->init_line();
        }
    }

    inline void init_line() {
        std::getline(this->file, this->line);
        if (this->line[0] != '>') {
            throw std::runtime_error("Invalid FASTA file -- must start with a record that begins with '>'");
        }
    }

public:
    Parser(const std::string& filename) {
        this->setup_file(filename);
    }

    ~Parser() {
        this->file.close();
    }

    inline bool eof() {
        return this->file.eof();
    }

    inline bool has_next() {
        return !(this->eof());
    };

    Record next();
    Record py_next();
    Records all();
    Records take(size_t n);
    void refresh();
    void fill();

    // need a header parser -> should be easy since can just use a find_if type of thing
};

#endif