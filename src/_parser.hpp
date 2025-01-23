#ifndef _PARSER_HPP
#define _PARSER_HPP

#include <fstream>
#include <string>
#include <vector>
#include <iostream>
#include <algorithm>

#define SEQLINESIZE 75
#define MINGENOMELEN 5000

enum RecordType {
    GENOME,
    GENE,
    PROTEIN,
    NUCLEOTIDE,
    UNKNOWN,
};

const RecordType DEFAULT_TYPE{ RecordType::UNKNOWN };
const std::string AMINO_ACID_DISCRIMINATORS { "*EFILPQX" };

struct Header {

private:
    inline void remove_record_delimiter() {
        if (this->name[0] == '>') {
            // BUG: if the header is just > without a name?
            this->name = this->name.substr(1);
        }
    }

    inline void split(const std::string& name) {
        std::size_t space_pos = name.find(' ');

        if (space_pos == std::string::npos) {
            this->name = name;
            this->desc = "";
        }
        else {
            this->name = name.substr(0, space_pos);
            this->desc = name.substr(space_pos + 1);
        }

        this->remove_record_delimiter();
    }

public:
    std::string name;
    std::string desc;

    // default constructor
    Header() : name(""), desc("") {}

    // copy constructor
    Header(const std::string& name, const std::string& desc) : name(name), desc(desc) {}

    // copy constructor to split name into fields
    Header(const std::string& name) { this->split(name); }

    // move constructor
    Header(std::string&& name, std::string&& desc) : name(std::move(name)), desc(std::move(desc)) {}

    // move constructor to split name into fields
    Header(std::string&& name) { this->split(std::move(name)); }

    bool operator==(const Header& other) const {
        return this->name == other.name && this->desc == other.desc;
    }

    bool operator!=(const Header& other) const {
        return !(*this == other);
    }

    inline void clean() { this->desc = ""; }

    inline bool empty() { return this->name.empty() && this->desc.empty(); }

    inline void clear() {
        this->name.clear();
        this->desc.clear();
    }

    // Return header as a string WITHOUT the > prefix
    inline std::string to_string() const {
        std::string str = this->name;

        if (!this->desc.empty()) {
            str += ' ';
            str += this->desc;
        }

        return str;
    }

    // return the total number of header characters
    inline size_t size() const { return this->name.size() + this->desc.size(); }
    
};


struct Record {
private:
    inline void read(std::istream& is, std::string& bufline) {
        if (bufline.empty()) {
            std::getline(is, bufline);
        }

        if (bufline[0] != '>') {
            // should throw an error but what if EOF?
            return;
        }

        this->header = Header{std::move(bufline)};

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
    }

    inline void detect_format() {
        for (char c : AMINO_ACID_DISCRIMINATORS) {
            // must be a protein
            if (this->seq.find(c) != std::string::npos) {
                this->type = RecordType::PROTEIN;
                return;
            }
        }

        // otherwise nucleotide seq, so it could be a gene or genome
        if (this->seq.size() >= MINGENOMELEN) {
            this->type = RecordType::GENOME;
        }
        else {
            this->type = RecordType::GENE;
        }
    }

public:
    Header header;
    std::string seq;
    RecordType type;

    // default constructor
    Record() : header(), seq(""), type(DEFAULT_TYPE) {}

    // copy constructor
    Record(const Record& other) : 
        header(other.header), seq(other.seq), type(other.type) {}

    // copy constructor with all 3 fields precomputed
    Record(const std::string& name, const std::string& desc, const std::string& seq, const RecordType& type = DEFAULT_TYPE) : 
        header(name, desc), seq(seq), type(type) {}

    // copy constructor that will split `name` at the first space into an actual name and description
    Record(const std::string& name, const std::string& seq, const RecordType& type = DEFAULT_TYPE) : 
        header(name), seq(seq), type(type) {}

    Record(const Header& header, const std::string& seq, const RecordType& type = DEFAULT_TYPE) : 
        header(header), seq(seq), type(type) {}

    // move constructor with all 3 fields precomputed
    Record(std::string&& name, std::string&& desc, std::string&& seq, const RecordType& type = DEFAULT_TYPE) : 
        header(std::move(name), std::move(desc)), seq(std::move(seq)), type(type) {}

    // move constructor that will split `name` at the first space into an actual name and description
    Record(std::string&& name, std::string&& seq, const RecordType& type = DEFAULT_TYPE) : 
        header(std::move(name)), seq(std::move(seq)), type(type) {}

    // constructor that reads from a stream
    Record(std::istream& is, std::string& bufline) {
        this->read(is, bufline);
    }
    
    // PUBLIC METHODS

    inline bool empty() {
        return this->header.empty() && this->seq.empty();
    }

    inline void clear() {
        this->header.clear();
        this->seq.clear();
    }

    inline void clean_header() { this->header.clean(); }

    inline void remove_stops() {
        if (this->type == RecordType::PROTEIN) {
            this->seq.erase(std::remove(this->seq.begin(), this->seq.end(), '*'), this->seq.end());
        }
    }

    std::string to_string() const {
        std::string str_record = ">";

        // account for the number of newlines needed for the sequence
        // +2 to round up AND account for newline between header and seq
        size_t num_seq_lines = this->seq.size() / SEQLINESIZE + 2;

        // preallocate the string buffer, +1 is for >
        str_record.reserve(this->seq.size() + this->header.size() + num_seq_lines + 1);

        str_record += this->header.to_string();
        str_record += '\n';

        for (size_t i = 0; i < this->seq.size(); i += SEQLINESIZE) {
            str_record += this->seq.substr(i, SEQLINESIZE);
            str_record += '\n';
        }

        return str_record;
    }

    friend std::ostream& operator<<(std::ostream& os, const Record& record) {
        return os << record.to_string();
    }

    bool operator==(const Record& other) const {
        // don't need to check type since it's derived from the sequence
        return this->header == other.header && this->seq == other.seq;
    }

    bool operator!=(const Record& other) const {
        return !(*this == other);
    }

};

using Records = std::vector<Record>;
using Headers = std::vector<Header>;

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

    void detect_format(const std::string& filename);

public:
    RecordType type;

    Parser(const std::string& filename) {
        this->setup_file(filename);
        this->detect_format(filename);
    }


    Parser(const std::string& filename, const RecordType& type) : type(type) {
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

    std::string& get_line() {
        return this->line;
    }

    Record next();
    Record py_next();
    Records all();
    Records take(size_t n);
    void refresh();
    size_t count();
    std::string extension();
    Header next_header();
    Header py_next_header();
    Headers headers();
};

#endif