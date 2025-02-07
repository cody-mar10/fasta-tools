#ifndef _PARSER_HPP
#define _PARSER_HPP

#include <fstream>
#include <string>
#include <vector>
#include <iostream>
#include <algorithm>

#define SEQLINESIZE 75
#define MINGENOMELEN 5000

using u_int32_t = unsigned int;

enum RecordType {
    GENOME,
    GENE,
    PROTEIN,
    NUCLEOTIDE,
    UNKNOWN,
};

const RecordType DEFAULT_TYPE{ RecordType::UNKNOWN };
const std::string AMINO_ACID_DISCRIMINATORS { "*EFILPQX" };

enum Strand {
    POSITIVE = 1,
    NEGATIVE = -1,
};

struct ProdigalHeader {
    using Fields = std::vector<std::string>;

    Fields split(const std::string& s, const std::string& delimiter) {
        Fields fields;
    
        size_t delimiter_size = delimiter.size();
        
        size_t last = 0;
        size_t next = 0;
        std::string token;

        while ((next = s.find(delimiter, last)) != std::string::npos) {
            token = s.substr(last, next-last);
            last = next + delimiter_size;
            fields.push_back(token);
        }

        // get last token
        token = s.substr(last);
        fields.push_back(token);

        return fields;
    }

    void init(const std::string& header) {
        Fields fields = this->split(header, " # ");

        // split name into scaffold and ptn number
        size_t pos = fields[0].rfind('_');

        this->scaffold = fields[0].substr(0, pos);
        this->id = std::stoi(fields[0].substr(pos + 1));
        this->start = std::stoi(fields[1]);
        this->end = std::stoi(fields[2]);
        this->strand = fields[3] == "1" ? Strand::POSITIVE : Strand::NEGATIVE;
        this->metadata = fields[4];
    }

public:
    std::string scaffold;
    u_int32_t id;
    u_int32_t start;
    u_int32_t end;
    Strand strand;
    std::string metadata; // TODO: could also parse this later

    ProdigalHeader() : ProdigalHeader("", 0, 0, 0, Strand::POSITIVE, "") {}

    ProdigalHeader(
        const std::string& scaffold, 
        const u_int32_t id, 
        u_int32_t start, 
        u_int32_t end, 
        Strand strand, 
        const std::string& metadata
    ) : 
        scaffold(scaffold), id(id), start(start), end(end), strand(strand), metadata(metadata) {}

    ProdigalHeader(const std::string& header) {
        this->init(header);
    }

    ProdigalHeader(std::string&& header) {
        this->init(std::move(header));
    }

    // ProdigalHeader(const Header& header) {
    //     ProdigalHeader(header.to_string());
    // }

    ProdigalHeader(const ProdigalHeader& other) : 
        scaffold(other.scaffold), id(other.id), start(other.start), end(other.end), strand(other.strand), metadata(other.metadata) {}

    // ProdigalHeader(const ProdigalHeader&& other) : 
    //     name(std::move(other.name)), start(other.start), end(other.end), strand(other.strand), metadata(std::move(other.metadata)) {}

    inline bool empty() const { 
        return this->scaffold.empty() && this->id == 0 && this->start == 0 && this->end == 0 && this->metadata.empty();
    }

    bool operator==(const ProdigalHeader other) const {
        // don't need to check type since it's derived from the sequence
        return this->scaffold == other.scaffold && this->id == other.id && this->start == other.start && this->end == other.end && this->strand == other.strand;
    }

    bool operator!=(const ProdigalHeader& other) const {
        return !(*this == other);
    }

    std::string to_string() const {
        std::string str = this->name();
        str += " # ";
        str += std::to_string(this->start);
        str += " # ";
        str += std::to_string(this->end);
        str += " # ";
        str += this->strand == Strand::POSITIVE ? "1" : "-1";
        str += " # ";
        str += this->metadata;
        return str;
    }

    inline std::string name() const {
        return this->scaffold + "_" + std::to_string(this->id);
    }
    
};

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

    /* 
    Check if the header is a Prodigal header.
    The prodigal header format is like this:
    `>scaffold_ptnnumber # start # end # strand # orfmetadata`
    */
    inline bool is_prodigal() const {
        size_t count = std::count_if(this->desc.begin(), this->desc.end(), [](char c) { return c == '#'; });

        return count == 4;
    }

    ProdigalHeader to_prodigal() const {
        if (!this->is_prodigal()) {
            throw std::runtime_error("Header is not a Prodigal header");
        }

        return ProdigalHeader(this->to_string());
    }
    
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
        header(name, desc), seq(seq), type(type) {
            if (this->type == DEFAULT_TYPE) {
                this->detect_format();
            }
        }

    // copy constructor that will split `name` at the first space into an actual name and description
    Record(const std::string& name, const std::string& seq, const RecordType& type = DEFAULT_TYPE) : 
        header(name), seq(seq), type(type) {
            if (this->type == DEFAULT_TYPE) {
                this->detect_format();
            }
        }

    Record(const Header& header, const std::string& seq, const RecordType& type = DEFAULT_TYPE) : 
        header(header), seq(seq), type(type) {
            if (this->type == DEFAULT_TYPE) {
                this->detect_format();
            }
        }

    // move constructor with all 3 fields precomputed
    Record(std::string&& name, std::string&& desc, std::string&& seq, const RecordType& type = DEFAULT_TYPE) : 
        header(std::move(name), std::move(desc)), seq(std::move(seq)), type(type) {
            if (this->type == DEFAULT_TYPE) {
                this->detect_format();
            }
        }

    // move constructor that will split `name` at the first space into an actual name and description
    Record(std::string&& name, std::string&& seq, const RecordType& type = DEFAULT_TYPE) : 
        header(std::move(name)), seq(std::move(seq)), type(type) {
            if (this->type == DEFAULT_TYPE) {
                this->detect_format();
            }
        }

    // constructor that reads from a stream
    Record(std::istream& is, std::string& bufline, const RecordType& type = DEFAULT_TYPE) : type(DEFAULT_TYPE) {
        this->read(is, bufline);

        if (this->type == DEFAULT_TYPE) {
            this->detect_format();
        }
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

    inline bool is_prodigal() const {
        return this->type == RecordType::PROTEIN && this->header.is_prodigal();
    }
};

using Records = std::vector<Record>;
using Headers = std::vector<Header>;
using ProdigalHeaders = std::vector<ProdigalHeader>;

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
    void check_if_prodigal();

public:
    RecordType type;
    bool is_prodigal;

    Parser(const std::string& filename, const RecordType& type = DEFAULT_TYPE) : type(type) {
        this->setup_file(filename);

        if (this->type == DEFAULT_TYPE) {
            // this will normally set is_prodigal
            this->detect_format(filename);
        } else {
            // so need to call this if the type is set
            this->check_if_prodigal();
        }
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
    ProdigalHeaders prodigal_headers();
    ProdigalHeader next_prodigal_header();
    ProdigalHeader py_next_prodigal_header();
};

#endif