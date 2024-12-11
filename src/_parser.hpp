#ifndef _PARSER_HPP
#define _PARSER_HPP

#include <fstream>
#include <string>
#include <tuple>
#include <vector>

struct Record {
private:
    inline std::pair<std::string, std::string> split(const std::string& name) {

        std::size_t space_pos = name.find(' ');

        if (space_pos == std::string::npos) {
            return std::make_pair(name, "");
        }

        return std::make_pair(name.substr(0, space_pos), name.substr(space_pos + 1));
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

    inline bool empty() {
        return this->name.empty() && this->desc.empty() && this->seq.empty();
    }

    inline void clear() {
        this->name.clear();
        this->desc.clear();
        this->seq.clear();
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

    inline bool has_next() {
        return !(this->file).eof();
    };

    Record next();
    Records all();
    Records take(size_t n);
    void refresh();
    void fill();

    // need a header parser -> should be easy since can just use a find_if type of thing
};

#endif